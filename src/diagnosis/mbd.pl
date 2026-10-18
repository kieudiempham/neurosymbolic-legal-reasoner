% Consistency-based model-based diagnosis for the cross-layer legal QA pipeline.
%
% Observations (asserted per query by mbd_engine.py):
%   required(C)          C is an unresolved input proposition on a path to the goal
%   checked(C)           C is a parser fact that the proof depends on (selected for verification)
%   parsed(C, pos|neg)   the parser produced C (true) or ~C
%   q(C, L)              NLI between the original question and the verbalised C, L in {entail, neutral, contra}
%   competing(R1, R2)    R1 and R2 are both applicable and conclude incompatible literals
%   resolution(R1, R2, yes|no)   result of symbolic KB verification for the pair
%
% A candidate diagnosis is a list of fault atoms:
%   missing(C) omission(C) misinterp(C) unsupported(C) overlap(R1,R2) kbconflict(R1,R2)
% The diagnostic model only constrains what each component must produce if it is
% normal or in a given fault mode; it never reads text and never ranks causes.

:- dynamic required/1, checked/1, parsed/2, q/2, competing/2, resolution/3.

relevant(C) :- required(C).
relevant(C) :- checked(C), \+ required(C).

% Question label: fixed when measured, otherwise any of the three labels.
label(C, L) :- q(C, L0), !, L = L0.
label(_, L) :- member(L, [entail, neutral, contra]).

obs_parse(C, P) :- parsed(C, P), !.
obs_parse(_, none).

user_mode(D, C, missing) :- memberchk(missing(C), D), !.
user_mode(_, _, ok).

parser_mode(D, C, M) :-
    member(F, D), F =.. [M, C], memberchk(M, [omission, misinterp, unsupported]), !.
parser_mode(_, _, ok).

% User layer: a normal user states every required proposition; a missing one is not in the question.
user_beh(ok, C, L) :- required(C), !, L \== neutral.
user_beh(ok, _, _).
user_beh(missing, _, neutral).

% Parser layer: a normal parser outputs exactly what the question states.
parser_beh(ok, entail, pos).
parser_beh(ok, contra, neg).
parser_beh(ok, neutral, none).
parser_beh(omission, L, none) :- L \== neutral.
parser_beh(misinterp, entail, neg).
parser_beh(misinterp, contra, pos).
parser_beh(unsupported, neutral, P) :- P \== none.

prop_consistent(D, C) :-
    user_mode(D, C, U), parser_mode(D, C, M), obs_parse(C, P),
    label(C, L), user_beh(U, C, L), parser_beh(M, L, P), !.

% KB layer: two applicable rules with incompatible conclusions are either a resolvable
% overlap (an encoded exception/priority exists) or an unresolved encoded-KB conflict.
kb_mode(D, R1, R2, overlap) :- memberchk(overlap(R1, R2), D), !.
kb_mode(D, R1, R2, kbconflict) :- memberchk(kbconflict(R1, R2), D), !.
kb_mode(_, _, _, ok).

res_obs(R1, R2, O) :- resolution(R1, R2, O), !.
res_obs(_, _, unknown).

kb_beh(overlap, yes).
kb_beh(overlap, unknown).
kb_beh(kbconflict, no).
kb_beh(kbconflict, unknown).

pair_consistent(D, R1, R2) :- kb_mode(D, R1, R2, M), res_obs(R1, R2, O), kb_beh(M, O).

well_formed(missing(C)) :- required(C).
well_formed(omission(C)) :- required(C).
well_formed(misinterp(C)) :- checked(C).
well_formed(unsupported(C)) :- checked(C).
well_formed(overlap(R1, R2)) :- competing(R1, R2).
well_formed(kbconflict(R1, R2)) :- competing(R1, R2).

consistent(D) :-
    forall(member(F, D), well_formed(F)),
    forall(relevant(C), prop_consistent(D, C)),
    forall(competing(R1, R2), pair_consistent(D, R1, R2)).

% Filter a list of candidates, keeping the consistent ones.
consistent_candidates(Cands, Kept) :- include(consistent, Cands, Kept).

% Set-minimal diagnoses by increasing cardinality, entirely inside Prolog.
% Atoms: candidate fault atoms; Key(F, K): component key so a component has at most one fault mode.
minimal_diagnoses(Atoms, MaxK, Minimal) :-
    numlist(0, MaxK, Ks),
    foldl(level(Atoms), Ks, [], Minimal).

level(Atoms, K, Found, Found1) :-
    findall(S, ( subset_k(K, Atoms, S),
                 one_mode_per_component(S),
                 \+ ( member(F, Found), subset_of(F, S) ),
                 consistent(S) ), New),
    append(Found, New, Found1).

subset_k(0, _, []) :- !.
subset_k(K, [X|Xs], [X|S]) :- K1 is K - 1, subset_k(K1, Xs, S).
subset_k(K, [_|Xs], S) :- K > 0, subset_k(K, Xs, S).

subset_of(A, B) :- forall(member(X, A), memberchk(X, B)).

component(missing(C), user(C)).
component(omission(C), parser(C)).
component(misinterp(C), parser(C)).
component(unsupported(C), parser(C)).
component(overlap(A, B), kb(A, B)).
component(kbconflict(A, B), kb(A, B)).

one_mode_per_component(S) :-
    maplist(component, S, Keys), sort(Keys, U), length(Keys, N), length(U, N).

% ---------------------------------------------------------------------------
% Persistent server mode (used by mbd_engine.py): one SWI-Prolog process answers
% many diagnosis requests. Each request replaces all observations, so requests are
% independent. Protocol on stdin/stdout:
%   request : diag(ObservationList, FaultAtoms, MaxK).
%   response: one write_canonical'd diagnosis per line, then the line 'END'
%             (or 'ERROR <message>' then 'END').
serve :-
    set_stream(user_output, buffer(line)),
    repeat,
    read_term(user_input, T, []),
    (   T == end_of_file
    ->  halt
    ;   catch(handle(T), E, (message_to_codes(E, Msg), format("ERROR ~s~n", [Msg]))),
        writeln('END'), flush_output, fail
    ).

message_to_codes(E, Codes) :- format(codes(Codes), "~q", [E]).

handle(diag(Obs, Atoms, K)) :-
    retractall(required(_)), retractall(checked(_)), retractall(parsed(_, _)),
    retractall(q(_, _)), retractall(competing(_, _)), retractall(resolution(_, _, _)),
    maplist(assertz, Obs),
    minimal_diagnoses(Atoms, K, Ds),
    forall(member(D, Ds), (write_canonical(D), nl)).
