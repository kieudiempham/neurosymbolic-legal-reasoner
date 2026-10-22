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
    Missing NLI observations (unverified measurements) leave the label free.

    Fault atoms (one mode per component):
      user layer    missing(C)        the question does not state C
      parser layer  omission(C)       the question states C (or its negation) but the parser did not output it
                    misinterp(C)      the parser output C with the wrong polarity / value
                    unsupported(C)    the parser output C although the question does not state it
      KB layer      misencoded(N)     the rule N does not say what its source text says
                    kbconflict(N1, N2)  two applicable rules conflict and no exception or priority resolves them
*/

:- dynamic required/1, presumed/1, checked/1, parsed/2, q/2, rule_used/1, kbtext/2, competing/2.

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
user_beh(ok, C, L) :- required(C), !, L \== neutral.
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

% Two competing applicable rules: consistent only if the pair is diagnosed as a conflict or one of the two
% rules is misencoded (a normal KB has no unresolved conflict).
pair_consistent(D, N1, N2) :-
    ( memberchk(kbconflict(N1, N2), D) ; memberchk(misencoded(N1), D) ; memberchk(misencoded(N2), D) ), !.

well_formed(missing(C)) :- required(C).
well_formed(omission(C)) :- ( required(C) ; presumed(C) ).
well_formed(misinterp(C)) :- checked(C).
well_formed(unsupported(C)) :- checked(C).
well_formed(misencoded(N)) :- rule_used(N).
well_formed(kbconflict(N1, N2)) :- competing(N1, N2).

consistent(D) :-
    forall(member(F, D), well_formed(F)),
    forall(relevant(C), prop_consistent(D, C)),
    forall(rule_used(N), rule_consistent(D, N)),
    forall(competing(N1, N2), pair_consistent(D, N1, N2)).

% Minimum-cardinality diagnoses: sizes 0, 1, ... up to MaxK, stopping at the first size that has any.
minimal_diagnoses(Atoms, MaxK, Minimal) :-
    numlist(0, MaxK, Ks),
    foldl(level(Atoms), Ks, [], Minimal).

level(_, _, Found, Found) :- Found \== [], !.
level(Atoms, K, Found, Found1) :-
    findall(S, ( subset_k(K, Atoms, S), one_mode_per_component(S),
                 \+ ( member(F, Found), subset_of(F, S) ), consistent(S) ), New),
    append(Found, New, Found1).

subset_k(0, _, []) :- !.
subset_k(K, [X|Xs], [X|S]) :- K1 is K - 1, subset_k(K1, Xs, S).
subset_k(K, [_|Xs], S) :- K > 0, subset_k(K, Xs, S).

subset_of(A, B) :- forall(member(X, A), memberchk(X, B)).

component(missing(C), user(C)).
component(omission(C), parser(C)).
component(misinterp(C), parser(C)).
component(unsupported(C), parser(C)).
component(misencoded(N), kb(N)).
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
    forall(member(P, [required/1, presumed/1, checked/1, parsed/2, q/2, rule_used/1, kbtext/2, competing/2]),
           ( P = F/A, functor(H, F, A), retractall(H) )),
    maplist(assertz, Obs),
    % symptoms: components whose observations contradict the assumption that everything works normally
    forall(( relevant(C), \+ prop_consistent([], C) ), format("SYMPTOM ~q~n", [C])),
    forall(( rule_used(N), \+ rule_consistent([], N) ), format("SYMPTOM ~q~n", [N])),
    forall(competing(N1, N2), format("SYMPTOM ~q~n", [N1-N2])),
    minimal_diagnoses(Atoms, K, Ds),
    forall(member(D, Ds), (write_canonical(D), nl)).
