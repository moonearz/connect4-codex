# Experimental results

Games alternate seats. Each pair shares seeds and, when enabled, a
four-ply random opening. Timings exclude initialization and opening moves.
This suite runs matches sequentially; wall time varies by machine.

| Agent A | Agent B | Opening plies | Games | A wins | B wins | Draws | A ms/move | B ms/move | Raw data |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| minimax | random | 0 | 20 | 20 | 0 | 0 | 3.861 | 0.003 | [minimax-random.json](minimax-random.json) |
| alphabeta | random | 0 | 20 | 20 | 0 | 0 | 13.561 | 0.004 | [alphabeta-random.json](alphabeta-random.json) |
| mcts | random | 0 | 20 | 20 | 0 | 0 | 17.504 | 0.003 | [mcts-random.json](mcts-random.json) |
| learned | random | 0 | 100 | 99 | 1 | 0 | 0.084 | 0.002 | [learned-random.json](learned-random.json) |
| untrained | random | 0 | 100 | 50 | 50 | 0 | 0.114 | 0.001 | [untrained-random.json](untrained-random.json) |
| learned | untrained | 0 | 100 | 92 | 8 | 0 | 0.085 | 0.090 | [learned-untrained.json](learned-untrained.json) |
| learned | minimax | 0 | 40 | 0 | 40 | 0 | 0.093 | 2.550 | [learned-minimax.json](learned-minimax.json) |
| learned | alphabeta | 0 | 40 | 0 | 40 | 0 | 0.111 | 14.962 | [learned-alphabeta.json](learned-alphabeta.json) |
| learned | mcts | 0 | 40 | 12 | 28 | 0 | 0.101 | 14.168 | [learned-mcts.json](learned-mcts.json) |
| alphabeta | minimax | 0 | 40 | 20 | 20 | 0 | 10.234 | 2.169 | [alphabeta-minimax.json](alphabeta-minimax.json) |
| alphabeta | mcts | 0 | 40 | 31 | 8 | 1 | 11.123 | 14.805 | [alphabeta-mcts.json](alphabeta-mcts.json) |
| mcts | minimax | 0 | 40 | 13 | 24 | 3 | 14.743 | 2.900 | [mcts-minimax.json](mcts-minimax.json) |
| alphabeta | minimax | 4 | 40 | 34 | 6 | 0 | 13.829 | 3.276 | [alphabeta-minimax-openings.json](alphabeta-minimax-openings.json) |
| learned | minimax | 4 | 40 | 8 | 32 | 0 | 0.162 | 5.267 | [learned-minimax-openings.json](learned-minimax-openings.json) |
| learned | alphabeta | 4 | 40 | 3 | 37 | 0 | 0.115 | 13.241 | [learned-alphabeta-openings.json](learned-alphabeta-openings.json) |

## Interpretation and limits

- The trained TD model wins 99/100 against random, compared with 50/100
  for the same architecture with zero weights. It wins 92/100 head-to-head
  against that untrained model, showing a benefit from experience.
- The learned model remains weaker than depth-limited search. Its eight
  aggregate features discard spatial relationships and tactical sequences.
- Empty-board deterministic search matchups repeat the same two games;
  their game counts do not represent independent samples. The additional
  paired-opening matches provide position diversity, but are still small.
- MCTS uses 300 uniform random rollouts per decision. This is a small
  budget with no rollout tactical policy or tree reuse.
- Both trained and untrained models value immediate terminal wins exactly;
  neither uses pretrained agents, solved databases or downloaded games.
- Depths and rollout counts are different computational budgets. This is
  a baseline comparison, not a matched-time algorithm ranking.
- Seeds 2026–2035 cover initial random-baseline matches; held-out
  evaluation uses seeds starting at 50000. Training uses seed 2026.
  Outcomes and move traces reproduce; timings and timing-based hashes vary.

## Next experiments

1. Run multiple training seeds and larger held-out opening suites.
2. Add shallow search over the learned value function and compare with
   equally budgeted handcrafted evaluation.
3. Add tactical rollout policies and tree reuse to MCTS.
4. Consider a small PyTorch value/policy network only after estimating
   CPU/GPU cost. It should retain held-out evaluations and an untrained
   control. No expensive neural training was run in this milestone.
