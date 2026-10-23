/*  First-order cross-layer model-based diagnosis (consistency-based, Reiter) for the legalkb pipeline.

    The components are read off the proofs of a run, so they are ground first-order atoms about the entities of
    the case and rules with variables (norm ids), not propositions fixed in advance per question:
      required(C)     C is a fact some proof still needs (a missing fact of a conditional answer)
      presumed(C)     C is an exception presumed absent because the case is silent about it
      checked(C)      C is a case fact a proof uses
      parsed(C, pos|neg|none)    what the parser produced for C
      q(C, L)         NLI between the question and the verbalised C, L in {entail, neutral, contra}
      rule_used(N)    norm N is a step of a certain proof
      kbtext(N, L)    NLI between the source text of N and the verbalised N
      competing(N1, N2)          two norms prove incompatible conclusions about the same entity
      near_miss(N)    norm N was not selected by step 2 although its text is close to the question
      rettext(N, L)   NLI between the text of N and the verbalised goal of the question
    Missing NLI observations (unverified measurements) leave the label free.

    Fault atoms (one mode per component):
      user layer    missing(C)        the question does not state C
      parser layer  omission(C)       the question states C (or its negation) but the parser did not output it
                    misinterp(C)      the parser output C with the wrong polarity / value
                    unsupported(C)    the parser output C although the question does not state it
      retrieval     omitted(N)        step 2 left out a norm that is about what the question asks
      KB layer      misencoded(N)     the rule N does not say what its source text says
                    kbconflict(N1, N2)  two applicable rules conflict and no exception or priority resolves them
*/

:- dynamic required/1, presumed/1, checked/1, parsed/2, q/2, rule_used/1, kbtext/2, competing/2, near_miss/1,
   rettext/2, needed/1, supports/3, selection_gap/1.

relevant(C) :- required(C).
relevant(C) :- presumed(C), \+ required(C).
relevant(C) :- checked(C), \+ required(C), \+ presumed(C).

label(C, L) :- q(C, L0), !, L = L0.
label(_, L) :- member(L, [entail, neutral, contra]).

obs_parse(C, P) :- parsed(C, P), !.
obs_parse(_, none).

user_mode(D, C, missing) :- memberchk(missing(C), D), !.
user_mode(_, _, ok).

parser_mode(D, C, M) :-
    member(F, D), F =.. [M, C], memberchk(M, [omission, misinterp, unsupported]), !.
parser_mode(_, _, ok).

% User layer: a normal user states every fact the answer needs; a missing one is not in the question.
user_beh(ok, C, L) :- (required(C); needed(C)), !, L \== neutral.
user_beh(ok, _, _).
user_beh(missing, _, neutral).

% Parser layer: a normal parser outputs exactly what the question states.
parser_beh(ok, entail, pos).
parser_beh(ok, contra, neg).
parser_beh(ok, neutral, none).
parser_beh(omission, L, none) :- L \== neutral.
parser_beh(misinterp, entail, neg).
parser_beh(misinterp, contra, pos).                   % also a wrong value: attr(hd, loai, a) where the text says b
parser_beh(unsupported, neutral, P) :- P \== none.

% An exception the case states false needs no parser output (it is presumed absent anyway).
prop_consistent(D, C) :-
    user_mode(D, C, U), parser_mode(D, C, M), obs_parse(C, P), label(C, L),
    (   U == ok, M == ok, presumed(C), P == none, L == contra -> true
    ;   user_beh(U, C, L), parser_beh(M, L, P) ), !.

% KB layer: a normal rule is entailed by its source text; a misencoded one is not.
kb_label(N, L) :- kbtext(N, L0), !, L = L0.
kb_label(_, L) :- member(L, [entail, neutral, contra]).

rule_consistent(D, N) :-
    kb_label(N, L),
    ( memberchk(misencoded(N), D) -> L \== entail ; L == entail ), !.

% Retrieval layer: a normal selection leaves out only norms that are not about the goal of the question.
ret_label(N, entail) :- selection_gap(N), !.
ret_label(N, L) :- rettext(N, L0), !, L = L0.
ret_label(_, L) :- member(L, [entail, neutral, contra]).

retrieval_consistent(D, N) :-
    ret_label(N, L),
    ( memberchk(omitted(N), D) -> L \== neutral ; L == neutral ), !.

% Two competing applicable rules: consistent only if the pair is diagnosed as a conflict or one of the two
% rules is misencoded (a normal KB has no unresolved conflict).
pair_consistent(D, N1, N2) :-
    ( memberchk(kbconflict(N1, N2), D) ; memberchk(misencoded(N1), D) ; memberchk(misencoded(N2), D)
    ; supports(N1, N2, C), parser_mode(D, C, M), M \== ok ), !.

well_formed(missing(C)) :- (required(C); needed(C)).
well_formed(omission(C)) :- ( required(C) ; presumed(C) ).
well_formed(misinterp(C)) :- checked(C).
well_formed(unsupported(C)) :- checked(C).
well_formed(misencoded(N)) :- rule_used(N).
well_formed(omitted(N)) :- near_miss(N).
well_formed(kbconflict(N1, N2)) :- competing(N1, N2).

consistent(D) :-
    one_mode_per_component(D),
    forall(member(F, D), well_formed(F)),
    forall(relevant(C), prop_consistent(D, C)),
    forall(rule_used(N), rule_consistent(D, N)),
    forall(near_miss(N), retrieval_consistent(D, N)),
    forall(competing(N1, N2), pair_consistent(D, N1, N2)).

% Checks: one per relevant atom, used rule, norm left out and competing pair; each involves only the fault atoms of
% its own components.
check(prop(C)) :- relevant(C).
check(rule(N)) :- rule_used(N).
check(ret(N)) :- near_miss(N).
check(pair(N1, N2)) :- competing(N1, N2).

check_ok(D, prop(C)) :- prop_consistent(D, C).
check_ok(D, rule(N)) :- rule_consistent(D, N).
check_ok(D, ret(N)) :- retrieval_consistent(D, N).
check_ok(D, pair(N1, N2)) :- pair_consistent(D, N1, N2).

% Conflicts (Reiter): a failing check cannot hold with all its components normal, so every diagnosis contains one
% of its repairs: the smallest sets of fault atoms that make that check hold without breaking a check that held.
conflict(Atoms, X, Repairs) :-
    check(X), \+ check_ok([], X),
    usable(Atoms, Us),
    findall([A], ( member(A, Us), check_ok([A], X) ), R1),
    findall(S, ( subset_k(2, Us, S), one_mode_per_component(S),
                 \+ (member(R, R1), subset_of(R, S)), check_ok(S, X) ), R2),
    append(R1, R2, Repairs).

usable(Atoms, Us) :-
    findall(A, ( member(A, Atoms), well_formed(A),
                 \+ ( check(Y), check_ok([], Y), \+ check_ok([A], Y) ) ), Us).

% Minimal diagnoses: the minimal hitting sets of the conflicts (each takes one repair of every conflict it does not
% already satisfy), at most MaxK fault atoms, kept when the whole model is consistent with them, then reduced to
% the subset-minimal ones. Unlike a search by size, a larger diagnosis is kept when no smaller one is contained in
% it, so the ranking (verify.py) sees every alternative.
minimal_diagnoses(Atoms, MaxK, Minimal) :-
    findall(X-R, conflict(Atoms, X, R), Cs),
    foldl(extend(MaxK), Cs, [[]], Hs),
    include(consistent, Hs, Ds),
    exclude(non_minimal(Ds), Ds, Minimal).

extend(MaxK, X-Repairs, Hs, Hs1) :-
    findall(S, ( member(H, Hs),
                 (   check_ok(H, X) -> S = H
                 ;   member(R, Repairs), append(R, H, S0), sort(S0, S), length(S, L), L =< MaxK,
                     one_mode_per_component(S) ) ), L0),
    sort(L0, Hs1).

non_minimal(Ds, D) :- member(E, Ds), E \== D, subset_of(E, D).

subset_k(0, _, []) :- !.
subset_k(K, [X|Xs], [X|S]) :- K1 is K - 1, subset_k(K1, Xs, S).
subset_k(K, [_|Xs], S) :- K > 0, subset_k(K, Xs, S).

subset_of(A, B) :- forall(member(X, A), memberchk(X, B)).

component(missing(C), user(C)).
component(omission(C), parser(C)).
component(misinterp(C), parser(C)).
component(unsupported(C), parser(C)).
component(misencoded(N), kb(N)).
component(omitted(N), retrieval(N)).
component(kbconflict(A, B), kb(A, B)).

one_mode_per_component(S) :-
    maplist(component, S, Keys), sort(Keys, U), length(Keys, N), length(U, N).

% Server: diag(Observations, FaultAtoms, MaxK).  ->  one diagnosis per line, then END
serve :-
    set_stream(user_output, buffer(line)),
    repeat,
    read_term(user_input, T, []),
    (   T == end_of_file -> halt
    ;   catch(handle(T), E, format("ERROR ~q~n", [E])),
        writeln('END'), flush_output, fail ).

handle(diag(Obs, Atoms, K)) :-
    forall(member(P, [required/1, presumed/1, checked/1, parsed/2, q/2, rule_used/1, kbtext/2, competing/2,
                      near_miss/1, rettext/2, needed/1, supports/3, selection_gap/1]),
           ( P = F/A, functor(H, F, A), retractall(H) )),
    maplist(assertz, Obs),
    % symptoms: components whose observations contradict the assumption that everything works normally
    forall(( relevant(C), \+ prop_consistent([], C) ), format("SYMPTOM ~q~n", [C])),
    forall(( rule_used(N), \+ rule_consistent([], N) ), format("SYMPTOM ~q~n", [N])),
    forall(competing(N1, N2), format("SYMPTOM ~q~n", [N1-N2])),
    forall(( near_miss(N), \+ retrieval_consistent([], N) ), format("SYMPTOM ~q~n", [N])),
    minimal_diagnoses(Atoms, K, Ds),
    forall(member(D, Ds), (write_canonical(D), nl)).
