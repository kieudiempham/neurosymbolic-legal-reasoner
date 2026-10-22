/*  First-order reasoner over the compiled legal KB (legal_kb.pl): a meta-interpreter that returns proof trees
    with the source norm of every rule step, and three-valued answers by abduction.

    A goal is
      certain      provable from the case facts alone;
      conditional  provable only if some missing case facts are assumed (they are listed: what to ask the user);
      not derived  not provable even with assumptions (no answer is returned for it).
    Exceptions the case says nothing about are presumed not to apply (negation of a goal that is provable only with
    assumptions succeeds, and the presumption is listed with the answer: "unless ...").

    Base predicates (no rule concludes them) are case facts. A missing ground base fact can be assumed unless the
    case states it is false (false_fact/1). A missing attribute value makes the comparison that uses it assumable.
    Entity types are not assumed (the parser has to give them). A goal met again inside its own proof is cut
    (a dependency cycle cannot loop).

    Server protocol (stdin/stdout, one request per line):
      q(Facts, FalseFacts, Goal, MaxMissing, Limit[, Allowed]).   ->  one JSON line with the answers, then END
    Allowed: the candidate norms of the question (step 2); a rule of another norm is not used. Default: all.
*/

:- use_module(library(http/json)).
:- use_module(library(solution_sequences)).
:- dynamic case_fact/1, false_fact/1, known_entity/1, allowed/1, restricted/0.

% ---------------------------------------------------------------------------------------------------- the case
load_case(Facts, FalseFacts) :-
    forall(retract(case_fact(F)), retract(F)),
    retractall(false_fact(_)), retractall(known_entity(_)),
    forall(member(F, Facts), (assertz(F), assertz(case_fact(F)), note_entities(F))),
    forall(member(F, FalseFacts), (assertz(false_fact(F)), note_entities(F))).

note_entities(F) :-
    F =.. [_|Args],
    forall((member(X, Args), atom(X), \+ known_entity(X)), assertz(known_entity(X))).

% ------------------------------------------------------------------------------------------- the interpreter
derived(G) :-
    functor(G, F, N), functor(H, F, N),
    predicate_property(H, number_of_rules(R)), R > 0.

source(G, Src) :-
    G =.. [F, N|_],
    memberchk(F, [applies, holds, obligation, right, prohibited, procedure, computed, sanction]),
    atom(N), !, Src = N.
source(_, derived).

unknown('$unknown'(_)).

missing_count(As, N) :- aggregate_all(count, member(missing(_), As), N).

assume(Atom, A0, [missing(Atom)|A0]) :-
    nb_getval(max_missing, Max), missing_count(A0, N), N < Max.

% prove(+Goal, -Proof, +Assumptions0, -Assumptions, +Ancestors)
prove(true, true, A, A, _) :- !.
prove(fail, _, _, _, _) :- !, fail.
prove((X, Y), and(PX, PY), A0, A, S) :- !, prove(X, PX, A0, A1, S), prove(Y, PY, A1, A, S).
prove((X ; Y), P, A0, A, S) :- !, ( prove(X, P, A0, A, S) ; prove(Y, P, A0, A, S) ).
prove(\+ X, P, A0, A, S) :- !, negation(X, P, A0, A, S).
prove(number(X), true, A, A, _) :- !, ( unknown(X) -> true ; number(X) ).
prove(G, P, A0, A, _) :- comparison(G), !, compare_goal(G, P, A0, A).
prove(V is E, P, A0, A, _) :- !,
    (   term_has_unknown(E) -> V = '$unknown'(E), P = missing(value(E)), A = A0
    ;   catch(V0 is E, _, fail), P = true, A = A0,
        ( float(V0), V0 =:= truncate(V0) -> V is truncate(V0) ; V = V0 ) ).  % 800000, not 8.0e+05
prove(attr(X, At, V), P, A0, A, _) :- !,
    (   \+ \+ attr(X, At, _) -> attr(X, At, V), P = fact(attr(X, At, V)), A = A0
    ;   atom(X), (known_entity(X) ; X == tham_so) -> V = '$unknown'(attr(X, At)), P = true, A = A0 ).
prove(G, P, A0, A, S) :- derived(G), !,
    \+ ( member(G0, S), G0 =@= G ),
    length(S, D), D < 60,
    clause(G, Body),
    source(G, Src),
    ( Src == derived ; \+ restricted ; allowed(Src) ),   % only the candidate norms of the question (step 2)
    prove(Body, PB, A0, A, [G|S]),
    P = node(G, Src, PB).
prove(G, P, A0, A, _) :-                       % base predicate: a case fact, or an assumable missing fact
    (   \+ \+ catch(call(G), _, fail) -> call(G), P = fact(G), A = A0
    ;   ground(G), \+ false_fact(G), \+ type_goal(G) -> assume(G, A0, A), P = missing(G) ).

type_goal(instance_of(_, _)).
type_goal(subtype(_, _)).

comparison(G) :- functor(G, F, 2), memberchk(F, [<, >, =<, >=, =:=, =\=, ==, \==]).

compare_goal(G, P, A0, A) :-
    G =.. [_, L, R],
    (   ( term_has_unknown(L) ; term_has_unknown(R) ) -> assume(G, A0, A), P = missing(G)
    ;   catch(call(G), _, fail), P = true, A = A0 ).

term_has_unknown(T) :- sub_term(U, T), compound(U), U = '$unknown'(_), !.

% \+ X: fails if X is provable from the facts; if X is provable only with assumptions, X is presumed false
% and the atoms it would need are recorded as presumed absent.
negation(X, P, A0, A, S) :-
    findall(As, limit(20, prove(X, _, [], As, S)), All),
    (   memberchk([], All) -> fail
    ;   All == [] -> P = true, A = A0
    ;   All = [First|_],
        findall(M, member(missing(M), First), Ms),
        P = presumed_absent(Ms), A = [presumed_absent(Ms)|A0] ).

% ------------------------------------------------------------------------------------------------ answers
solve(Goal, Max, Limit, Answers) :-
    nb_setval(max_missing, Max),
    findall(Goal-Proof-As, limit(Limit, distinct(Goal-K, (prove(Goal, Proof, [], As, []), key(As, K)))), Rs),
    maplist(answer, Rs, Answers0),
    % a conclusion that is certain needs no conditional alternatives
    exclude(superseded(Answers0), Answers0, Answers1),
    sort(missing_n, @=<, Answers1, Answers).

superseded(All, A) :-
    get_dict(status, A, conditional), get_dict(goal, A, G),
    member(B, All), get_dict(status, B, certain), get_dict(goal, B, G), !.

key(As, K) :- msort(As, K).

answer(Goal-Proof-As, _{goal: G, status: St, missing: Ms, presumed_absent: Ps, missing_n: N, proof: T}) :-
    findall(S, (member(missing(M), As), show(M, S)), Ms0), sort(Ms0, Ms),
    findall(S, (member(presumed_absent(L), As), member(M, L), show(M, S)), Ps0), sort(Ps0, Ps),
    length(Ms, N),
    ( N =:= 0 -> St = certain ; St = conditional ),
    show(Goal, G),
    tree(Proof, Ts), ( Ts = [T] -> true ; T = _{goal: "true", children: Ts} ).

show(T, S) :-
    copy_term(T, C0), plain(C0, C), numbervars(C, 0, _),
    format(string(S), "~W", [C, [quoted(true), numbervars(true)]]).

% '$unknown'(attr(hd, thoi_han)) >= 1  ->  attr(hd, thoi_han) >= 1 (a value the case does not give)
plain(T, T) :- var(T), !.
plain('$unknown'(X), Y) :- !, plain(X, Y).
plain(T, T) :- atomic(T), !.
plain(T, P) :- T =.. [F|As], maplist(plain, As, Ps), P =.. [F|Ps].

% proof term -> list of JSON nodes (conjunctions flattened, arithmetic and type steps dropped)
tree(true, []) :- !.
tree(and(X, Y), Ts) :- !, tree(X, A), tree(Y, B), append(A, B, Ts).
tree(fact(G), [_{goal: S, kind: fact}]) :- !, show(G, S).
tree(missing(G), [_{goal: S, kind: missing}]) :- !, show(G, S).
tree(presumed_absent(Ms), [_{goal: S, kind: presumed_absent}]) :- !,
    findall(X, (member(M, Ms), show(M, X)), Xs), atomic_list_concat(Xs, ', ', S).
tree(node(G, _, _), []) :- functor(G, F, _), memberchk(F, [is_a, subtype_star]), !.
tree(node(G, Src, PB), [_{goal: S, norm: Src, kind: rule, children: Cs}]) :- show(G, S), tree(PB, Cs).

% ------------------------------------------------------------------------------------------------- server
serve :-
    set_stream(user_output, encoding(utf8)), set_stream(user_input, encoding(utf8)),
    repeat,
    read_term(user_input, T, []),
    (   T == end_of_file -> !
    ;   catch(handle(T), E, (print_message(error, E), format("ERROR ~q~n", [E]))),
        format("END~n"), flush_output, fail ).

handle(q(Facts, FalseFacts, Goal, Max, Limit)) :- handle(q(Facts, FalseFacts, Goal, Max, Limit, all)).
handle(q(Facts, FalseFacts, Goal, Max, Limit, Allowed)) :-
    retractall(allowed(_)), retractall(restricted),
    ( Allowed == all -> true ; assertz(restricted), forall(member(N, Allowed), assertz(allowed(N))) ),
    load_case(Facts, FalseFacts),
    solve(Goal, Max, Limit, Answers),
    json_write_dict(user_output, _{answers: Answers}, [width(0)]), nl.
