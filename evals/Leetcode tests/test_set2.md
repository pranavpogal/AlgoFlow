problem_number: 55
title: Jump Game
difficulty: Medium
description: You are given an integer array nums where nums[i] represents the maximum jump length from index i. Return true if you can reach the last index.
expected_topic: Greedy
expected_pattern: Farthest Reach Greedy
expected_sub_patterns: Reachability Frontier, Running Maximum, Local State Compression
expected_prerequisites: Arrays, Greedy Reasoning, Reachability
notes: Important Greedy-vs-DP discriminator. A DP formulation is possible, but the canonical optimal approach tracks only the farthest reachable index. AlgoFlow should not classify every forward state transition as DP.

problem_number: 45
title: Jump Game II
difficulty: Medium
description: You are given a 0-indexed array nums where nums[i] represents the maximum jump length from index i. Return the minimum number of jumps required to reach the last index.
expected_topic: Greedy
expected_pattern: Greedy Level Expansion
expected_sub_patterns: Current Range Boundary, Farthest Next Reach, Implicit BFS Layers
expected_prerequisites: Arrays, Greedy Reasoning, Range Tracking
notes: Strong confusion case. The word minimum and transition-like structure may suggest DP, but the optimal approach greedily expands reachable ranges.

problem_number: 134
title: Gas Station
difficulty: Medium
description: There are n gas stations arranged in a circle. Given arrays gas and cost, return the starting station index from which you can travel around the circuit once, or -1 if impossible.
expected_topic: Greedy
expected_pattern: Greedy Reset
expected_sub_patterns: Running Balance, Global Feasibility, Candidate Elimination
expected_prerequisites: Arrays, Greedy Reasoning, Prefix Balance
notes: Strong Greedy-vs-DP test. Failure from a candidate start eliminates an entire range of earlier candidates.

problem_number: 435
title: Non-overlapping Intervals
difficulty: Medium
description: Given an array of intervals, return the minimum number of intervals that must be removed so that the remaining intervals do not overlap.
expected_topic: Greedy
expected_pattern: Earliest Finish Time
expected_sub_patterns: Interval Scheduling, Sort by End Time, Maximum Compatible Subset
expected_prerequisites: Sorting, Intervals, Greedy Reasoning
notes: Critical Greedy-vs-LIS discriminator. The problem asks for a maximum compatible ordered subset, which may tempt LIS-style reasoning, but earliest finishing time gives the canonical greedy solution.

problem_number: 452
title: Minimum Number of Arrows to Burst Balloons
difficulty: Medium
description: Given intervals representing horizontal balloon diameters, return the minimum number of arrows required to burst all balloons.
expected_topic: Greedy
expected_pattern: Interval Endpoint Greedy
expected_sub_patterns: Sort by End Coordinate, Maximum Overlap Reuse, Interval Covering
expected_prerequisites: Sorting, Intervals, Greedy Reasoning
notes: Similar surface structure to interval DP, but the locally optimal earliest endpoint choice is globally safe.

problem_number: 763
title: Partition Labels
difficulty: Medium
description: Given a string s, partition it into as many parts as possible so that each letter appears in at most one part. Return the sizes of the parts.
expected_topic: Greedy
expected_pattern: Greedy Boundary Expansion
expected_sub_patterns: Last Occurrence Tracking, Dynamic Segment Boundary, Partition Closure
expected_prerequisites: Strings, Arrays or Hash Maps, Greedy Reasoning
notes: Useful non-numeric greedy test. No sorting is involved, preventing AlgoFlow from equating Greedy only with sorted inputs.

problem_number: 1029
title: Two City Scheduling
difficulty: Medium
description: A company plans to interview 2n people. Given the cost of flying each person to city A and city B, send exactly n people to each city while minimizing total cost.
expected_topic: Greedy
expected_pattern: Sort by Opportunity Cost
expected_sub_patterns: Cost Difference Ordering, Relative Advantage, Balanced Assignment
expected_prerequisites: Sorting, Greedy Reasoning, Arrays
notes: Strong discriminator. The decision is based on relative cost difference rather than independent minimum choices or DP states.

problem_number: 881
title: Boats to Save People
difficulty: Medium
description: Given an array people where people[i] is the weight of the ith person and a weight limit per boat, each boat carries at most two people. Return the minimum number of boats needed.
expected_topic: Greedy
expected_pattern: Sort and Two Pointers
expected_sub_patterns: Pair Heaviest with Lightest, Extremal Choice, Capacity Matching
expected_prerequisites: Sorting, Two Pointers, Greedy Reasoning
notes: Tests whether AlgoFlow recognizes a greedy pairing invariant rather than generic two-pointer classification alone.

problem_number: 621
title: Task Scheduler
difficulty: Medium
description: Given tasks represented by capital letters and a non-negative cooling interval n, return the minimum number of CPU intervals required to finish all tasks.
expected_topic: Greedy
expected_pattern: Frequency-Based Greedy Scheduling
expected_sub_patterns: Maximum Frequency Bottleneck, Idle Slot Counting, Priority Queue Alternative
expected_prerequisites: Frequency Counting, Greedy Reasoning, Heaps
notes: Good architecture stress case because scheduling problems often trigger DP incorrectly.

problem_number: 646
title: Maximum Length of Pair Chain
difficulty: Medium
description: You are given pairs where pairs[i] = [left_i, right_i] and left_i < right_i. A pair p2 can follow p1 if p1[1] < p2[0]. Return the length of the longest chain.
expected_topic: Greedy
expected_pattern: Earliest Finish Time
expected_sub_patterns: Interval Scheduling, Sort by Right Endpoint, DP Alternative
expected_prerequisites: Sorting, Intervals, Greedy Reasoning
notes: Major Greedy-vs-DP-vs-LIS trap. The phrase longest chain strongly resembles LIS, and DP is valid, but the canonical optimal approach is greedy by earliest ending pair.

problem_number: 376
title: Wiggle Subsequence
difficulty: Medium
description: Given an integer array nums, return the length of the longest subsequence whose consecutive differences strictly alternate between positive and negative.
expected_topic: Greedy
expected_pattern: Greedy Trend Tracking
expected_sub_patterns: Peak-Valley Selection, Sign Change Detection, Constant-State Compression, DP Alternative
expected_prerequisites: Arrays, Subsequences, Greedy Reasoning
notes: Extremely valuable confusion case. The word longest subsequence may trigger LIS or DP, but a greedy peak-valley interpretation gives the optimal solution.

problem_number: 122
title: Best Time to Buy and Sell Stock II
difficulty: Medium
description: Given an array prices where prices[i] is the stock price on day i, you may complete as many transactions as desired while holding at most one stock at a time. Return the maximum profit.
expected_topic: Greedy
expected_pattern: Accumulate Positive Gains
expected_sub_patterns: Local Profit Capture, Monotonic Segment Decomposition, DP Alternative
expected_prerequisites: Arrays, Greedy Reasoning
notes: Strong Greedy-vs-DP discriminator because stock problems frequently suggest state-machine DP, but unlimited transactions collapse into a greedy solution.

problem_number: 198
title: House Robber
difficulty: Medium
description: Given an integer array nums where nums[i] represents money in house i, return the maximum amount that can be robbed without robbing two adjacent houses.
expected_topic: Dynamic Programming
expected_pattern: Take-or-Skip DP
expected_sub_patterns: Include-Exclude Decision, Linear DP, State Compression
expected_prerequisites: Arrays, Dynamic Programming
notes: DP control case. Greedy selection of the locally largest available house can block a better global combination.

problem_number: 213
title: House Robber II
difficulty: Medium
description: Houses are arranged in a circle, and adjacent houses cannot both be robbed. Return the maximum amount of money that can be robbed.
expected_topic: Dynamic Programming
expected_pattern: Circular Case Reduction to Linear DP
expected_sub_patterns: Two Scenario Decomposition, Take-or-Skip DP, State Compression
expected_prerequisites: Linear DP, Arrays, Circular Constraints
notes: Tests whether AlgoFlow recognizes that a global circular dependency requires case decomposition rather than greedy selection.

problem_number: 322
title: Coin Change
difficulty: Medium
description: Given coin denominations and an amount, return the fewest number of coins required to make that amount, or -1 if it cannot be formed.
expected_topic: Dynamic Programming
expected_pattern: Unbounded Knapsack DP
expected_sub_patterns: Minimum-State Transition, Reusable Choices, Bottom-Up DP
expected_prerequisites: Dynamic Programming, Arrays, Optimization Problems
notes: Essential Greedy-vs-DP trap. Choosing the largest coin first is not correct for arbitrary coin systems.

problem_number: 139
title: Word Break
difficulty: Medium
description: Given a string s and a dictionary of strings wordDict, return true if s can be segmented into a space-separated sequence of one or more dictionary words.
expected_topic: Dynamic Programming
expected_pattern: Prefix Segmentation DP
expected_sub_patterns: Reachable Prefix States, Dictionary Lookup, Partition DP
expected_prerequisites: Strings, Hash Sets, Dynamic Programming
notes: Tests whether AlgoFlow recognizes overlapping prefix feasibility states rather than greedy longest-word matching.

problem_number: 91
title: Decode Ways
difficulty: Medium
description: Given a string of digits, return the number of ways to decode it using mappings from 1 through 26 to letters.
expected_topic: Dynamic Programming
expected_pattern: Prefix Counting DP
expected_sub_patterns: One-Character Transition, Two-Character Transition, Rolling State
expected_prerequisites: Strings, Dynamic Programming
notes: DP control problem. Local decoding choices branch and overlap, making greedy commitment invalid.

problem_number: 416
title: Partition Equal Subset Sum
difficulty: Medium
description: Given an integer array nums, return true if the array can be partitioned into two subsets with equal sum.
expected_topic: Dynamic Programming
expected_pattern: 0/1 Knapsack
expected_sub_patterns: Subset Sum, Boolean State Reachability, Space Optimization
expected_prerequisites: Dynamic Programming, Subset Sum, Arrays
notes: Important DP-vs-Greedy discriminator. Sorting and greedily balancing subsets does not guarantee correctness.

problem_number: 300
title: Longest Increasing Subsequence
difficulty: Medium
description: Given an integer array nums, return the length of the longest strictly increasing subsequence.
expected_topic: Dynamic Programming and Binary Search
expected_pattern: Longest Increasing Subsequence
expected_sub_patterns: O(n^2) DP, Patience Sorting, Tails Array, Binary Search Optimization
expected_prerequisites: Subsequences, Dynamic Programming, Binary Search
notes: Primary LIS control case. AlgoFlow should identify true subsequence-order structure and distinguish it from generic greedy sequence problems.

problem_number: 673
title: Number of Longest Increasing Subsequence
difficulty: Medium
description: Given an integer array nums, return the number of longest increasing subsequences.
expected_topic: Dynamic Programming
expected_pattern: LIS with Count Tracking
expected_sub_patterns: Length DP, Count DP, Predecessor Aggregation
expected_prerequisites: Longest Increasing Subsequence, Dynamic Programming
notes: Strong LIS control. Patience sorting alone does not directly provide the required count.

problem_number: 354
title: Russian Doll Envelopes
difficulty: Hard
description: Given envelopes where envelopes[i] = [width_i, height_i], return the maximum number of envelopes that can be nested inside one another. An envelope fits only if both dimensions are strictly larger.
expected_topic: Dynamic Programming and Binary Search
expected_pattern: Sort and Reduce to LIS
expected_sub_patterns: Width Ascending Sort, Height Descending Tie-Break, LIS on Second Dimension
expected_prerequisites: Sorting, Longest Increasing Subsequence, Binary Search
notes: Critical LIS transfer case. Tests whether AlgoFlow can recognize a hidden LIS after a nontrivial sorting transformation.

problem_number: 1626
title: Best Team With No Conflicts
difficulty: Medium
description: Choose players with scores and ages to maximize total score such that no younger player has a strictly higher score than an older player.
expected_topic: Dynamic Programming
expected_pattern: Weighted LIS
expected_sub_patterns: Sort Then DP, Maximum-Sum Increasing Subsequence, Compatibility Transition
expected_prerequisites: Sorting, Dynamic Programming, LIS Variants
notes: Excellent LIS-vs-Greedy discriminator. The objective is maximum total score rather than maximum subsequence length, requiring weighted DP.

problem_number: 1235
title: Maximum Profit in Job Scheduling
difficulty: Hard
description: Given jobs with start times, end times, and profits, select non-overlapping jobs to maximize total profit.
expected_topic: Dynamic Programming and Binary Search
expected_pattern: Weighted Interval Scheduling
expected_sub_patterns: Sort by Time, Binary Search Previous Compatible Job, Take-or-Skip DP
expected_prerequisites: Dynamic Programming, Binary Search, Intervals
notes: One of the strongest Greedy-vs-DP tests. Unweighted interval scheduling is greedy, but adding profits destroys the earliest-finish greedy rule.

problem_number: 1143
title: Longest Common Subsequence
difficulty: Medium
description: Given two strings text1 and text2, return the length of their longest common subsequence.
expected_topic: Dynamic Programming
expected_pattern: Two-Sequence DP
expected_sub_patterns: Match-or-Skip Transition, 2D DP, Space Optimization
expected_prerequisites: Strings, Dynamic Programming, Subsequences
notes: Useful anti-LIS control. The word longest subsequence appears, but this is LCS rather than LIS and requires two-sequence state reasoning.