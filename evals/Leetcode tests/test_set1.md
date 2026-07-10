problem_number: 1
title: Two Sum
difficulty: Easy
description: Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target. You may assume that each input has exactly one solution, and you may not use the same element twice.
expected_topic: Arrays and Hashing
expected_pattern: Hash Map Lookup
expected_sub_patterns: Complement Search, One-Pass Hashing
expected_prerequisites: Arrays, Hash Maps, Time Complexity
notes: Common baseline problem. Tests whether AlgoFlow recognizes complement lookup instead of brute force.

problem_number: 20
title: Valid Parentheses
difficulty: Easy
description: Given a string s containing only the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid. Open brackets must be closed by the same type of brackets and in the correct order.
expected_topic: Stack
expected_pattern: Stack-Based Matching
expected_sub_patterns: LIFO Processing, Pair Validation
expected_prerequisites: Stack, Strings
notes: Common baseline problem with a highly recognizable stack pattern.

problem_number: 53
title: Maximum Subarray
difficulty: Medium
description: Given an integer array nums, find the contiguous subarray with the largest sum and return its sum.
expected_topic: Dynamic Programming
expected_pattern: Kadane's Algorithm
expected_sub_patterns: Running State Optimization, Local vs Global Optimum
expected_prerequisites: Arrays, Dynamic Programming
notes: Tests recognition of a classic one-dimensional DP optimization pattern.

problem_number: 200
title: Number of Islands
difficulty: Medium
description: Given an m x n binary grid where '1' represents land and '0' represents water, return the number of islands. An island is formed by connecting adjacent lands horizontally or vertically.
expected_topic: Graphs
expected_pattern: Connected Components Traversal
expected_sub_patterns: DFS, BFS, Grid Traversal, Flood Fill
expected_prerequisites: Graph Traversal, Recursion or Queue, 2D Arrays
notes: Common graph baseline. Multiple valid traversal implementations should be accepted.

problem_number: 198
title: House Robber
difficulty: Medium
description: You are given an integer array nums representing the amount of money in each house. Adjacent houses cannot be robbed on the same night. Return the maximum amount of money you can rob.
expected_topic: Dynamic Programming
expected_pattern: Take-or-Skip DP
expected_sub_patterns: State Compression, Linear DP
expected_prerequisites: Arrays, Dynamic Programming
notes: Tests whether AlgoFlow identifies mutually exclusive adjacent choices.

problem_number: 875
title: Koko Eating Bananas
difficulty: Medium
description: You are given an integer array piles, where piles[i] is the number of bananas in the ith pile, and an integer h. Return the minimum integer eating speed k such that all bananas can be eaten within h hours.
expected_topic: Binary Search
expected_pattern: Binary Search on Answer
expected_sub_patterns: Monotonic Feasibility Check, Search Space Reduction
expected_prerequisites: Binary Search, Ceiling Division, Time Complexity
notes: Tests recognition of binary search over an answer space rather than over array indices.

problem_number: 3
title: Longest Substring Without Repeating Characters
difficulty: Medium
description: Given a string s, find the length of the longest substring without repeating characters.
expected_topic: Sliding Window
expected_pattern: Variable-Size Sliding Window
expected_sub_patterns: Frequency Tracking, Last-Seen Index, Two Pointers
expected_prerequisites: Strings, Hash Maps or Hash Sets, Two Pointers
notes: Common sliding-window baseline.

problem_number: 207
title: Course Schedule
difficulty: Medium
description: There are numCourses courses labeled from 0 to numCourses - 1. Given prerequisite pairs, determine whether it is possible to finish all courses.
expected_topic: Graphs
expected_pattern: Cycle Detection in Directed Graph
expected_sub_patterns: Topological Sort, Kahn's Algorithm, DFS Coloring
expected_prerequisites: Directed Graphs, DFS or BFS, Indegree
notes: Multiple valid graph approaches should be accepted.

problem_number: 128
title: Longest Consecutive Sequence
difficulty: Medium
description: Given an unsorted array of integers nums, return the length of the longest consecutive elements sequence. You must write an algorithm that runs in O(n) time.
expected_topic: Arrays and Hashing
expected_pattern: Hash Set Sequence Expansion
expected_sub_patterns: Sequence-Start Detection, O(n) Expected Lookup, Union Find as Alternative
expected_prerequisites: Hash Sets, Amortized Complexity, Arrays
notes: Important constraint trap. Sorting plus pointers is logically plausible but violates the required O(n) time complexity. Good test for complexity-aware pattern rejection.

problem_number: 560
title: Subarray Sum Equals K
difficulty: Medium
description: Given an integer array nums and an integer k, return the total number of subarrays whose sum equals k. The array may contain positive, zero, and negative integers.
expected_topic: Prefix Sum and Hashing
expected_pattern: Prefix Sum Frequency Map
expected_sub_patterns: Running Prefix Sum, Complement Frequency Lookup
expected_prerequisites: Prefix Sums, Hash Maps, Subarray Reasoning
notes: Deceptive sliding-window trap. Negative numbers invalidate standard monotonic sliding-window reasoning.

problem_number: 287
title: Find the Duplicate Number
difficulty: Medium
description: Given an array nums containing n + 1 integers where each integer is in the range [1, n], return the repeated number. Solve the problem without modifying nums and using only O(1) extra space.
expected_topic: Linked List and Array Reasoning
expected_pattern: Floyd's Cycle Detection
expected_sub_patterns: Array-as-Functional-Graph, Slow and Fast Pointers, Cycle Entry Detection
expected_prerequisites: Two Pointers, Linked List Cycle Detection, Array Indexing
notes: Highly deceptive. The input is an array, but the optimal solution models values as pointers in an implicit linked structure.

problem_number: 41
title: First Missing Positive
difficulty: Hard
description: Given an unsorted integer array nums, return the smallest missing positive integer. You must implement an algorithm that runs in O(n) time and uses O(1) auxiliary space.
expected_topic: Arrays
expected_pattern: Cyclic Placement
expected_sub_patterns: Index-as-Hash, In-Place Rearrangement, Value-to-Index Mapping
expected_prerequisites: Arrays, In-Place Algorithms, Index Manipulation
notes: Strong constraint-driven problem. Hash sets violate O(1) space and sorting violates O(n) time.

problem_number: 42
title: Trapping Rain Water
difficulty: Hard
description: Given n non-negative integers representing an elevation map where the width of each bar is 1, compute how much water can be trapped after raining.
expected_topic: Arrays and Two Pointers
expected_pattern: Two-Pointer Boundary Compression
expected_sub_patterns: Left Maximum, Right Maximum, Monotonic Stack Alternative, Prefix-Suffix Alternative
expected_prerequisites: Arrays, Two Pointers, Prefix Maximums
notes: Multi-pattern problem. AlgoFlow should ideally distinguish the optimal-space two-pointer solution from other valid approaches.

problem_number: 134
title: Gas Station
difficulty: Medium
description: There are n gas stations arranged in a circle. Given arrays gas and cost, return the starting station index from which you can travel around the circuit once, or -1 if impossible.
expected_topic: Greedy
expected_pattern: Greedy Reset
expected_sub_patterns: Global Feasibility, Running Balance, Candidate Elimination
expected_prerequisites: Arrays, Greedy Reasoning, Prefix Balance
notes: Tests whether AlgoFlow can recognize a greedy proof rather than simulation from every starting point.

problem_number: 739
title: Daily Temperatures
difficulty: Medium
description: Given an array temperatures, return an array answer such that answer[i] is the number of days you must wait after day i to get a warmer temperature. If no future day exists, set answer[i] to 0.
expected_topic: Stack
expected_pattern: Monotonic Stack
expected_sub_patterns: Next Greater Element, Index Stack, Deferred Resolution
expected_prerequisites: Stack, Arrays
notes: Strong baseline for monotonic-stack recognition.

problem_number: 684
title: Redundant Connection
difficulty: Medium
description: You are given a graph that started as a tree with n nodes, then one additional edge was added. Return an edge that can be removed so the resulting graph is a tree.
expected_topic: Graphs
expected_pattern: Union Find
expected_sub_patterns: Disjoint Set Union, Cycle Detection, Path Compression, Union by Rank or Size
expected_prerequisites: Graphs, Trees, Disjoint Sets
notes: Clean Union-Find baseline. Useful for checking whether AlgoFlow recognizes DSU when connectivity evolves edge by edge.

problem_number: 721
title: Accounts Merge
difficulty: Medium
description: Given a list of accounts where each account contains a name followed by email addresses, merge accounts that belong to the same person. Two accounts belong to the same person if they share at least one common email.
expected_topic: Graphs and Disjoint Sets
expected_pattern: Union Find
expected_sub_patterns: Connected Components, Identifier Mapping, Hash Map Indexing
expected_prerequisites: Hash Maps, Graph Connectivity, Disjoint Set Union
notes: Less obvious DSU problem because the entities are emails and accounts rather than numbered graph nodes.

problem_number: 76
title: Minimum Window Substring
difficulty: Hard
description: Given strings s and t, return the minimum window substring of s such that every character in t, including duplicates, is included in the window. Return an empty string if no such substring exists.
expected_topic: Sliding Window
expected_pattern: Variable-Size Sliding Window
expected_sub_patterns: Frequency Deficit Tracking, Expand-and-Shrink, Validity Counter
expected_prerequisites: Strings, Hash Maps, Two Pointers
notes: Harder sliding-window test requiring multiplicity-aware frequency tracking.

problem_number: 410
title: Split Array Largest Sum
difficulty: Hard
description: Given an integer array nums and an integer k, split nums into k non-empty contiguous subarrays such that the largest subarray sum is minimized. Return that minimized largest sum.
expected_topic: Binary Search
expected_pattern: Binary Search on Answer
expected_sub_patterns: Greedy Feasibility Check, Minimize Maximum, Monotonic Predicate
expected_prerequisites: Binary Search, Greedy Validation, Prefix Reasoning
notes: Excellent architecture test. The word 'split' may suggest DP, but monotonic feasibility enables binary search on the answer.

problem_number: 301
title: Remove Invalid Parentheses
difficulty: Hard
description: Given a string containing parentheses and lowercase letters, remove the minimum number of invalid parentheses to make the string valid. Return all possible valid strings with the minimum number of removals.
expected_topic: Graph Search and Backtracking
expected_pattern: BFS by Removal Level
expected_sub_patterns: State-Space Search, Minimum-Level Discovery, Deduplication, Backtracking Alternative
expected_prerequisites: BFS, Sets, Strings, Parentheses Validation
notes: Unique state-space problem. BFS naturally guarantees minimum removals by exploring deletion levels.