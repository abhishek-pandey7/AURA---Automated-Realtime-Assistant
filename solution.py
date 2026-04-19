from typing import List

class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        """
        Finds two numbers in the array that add up to the target.
        Time Complexity: O(n)
        Space Complexity: O(n)
        """
        prevMap = {}  # val : index

        for i, n in enumerate(nums):
            diff = target - n
            if diff in prevMap:
                return [prevMap[diff], i]
            prevMap[n] = i
        return []

# Test cases to verify the implementation
if __name__ == "__main__":
    sol = Solution()
    
    # Test Case 1
    assert sol.twoSum([2, 7, 11, 15], 9) == [0, 1]
    # Test Case 2
    assert sol.twoSum([3, 2, 4], 6) == [1, 2]
    # Test Case 3
    assert sol.twoSum([3, 3], 6) == [0, 1]
    
    print("All test cases passed!")
