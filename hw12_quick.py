import numpy as np
'''
code to solve for optimal U0 for lab question 3H
'''
B0 = np.array([[1,10],[1,10],[10,1],[1,10],[10,1]])
Z0 = np.array([[1],[1],[5],[1],[5]])

B0_squared = np.dot(np.transpose(B0),B0)
solution = np.linalg.inv(B0_squared + np.identity(np.shape(B0_squared)[0])) 
solution = np.dot(solution,np.transpose(B0))
solution = np.dot(solution,Z0)

print(solution)
print(f"predicted rating for llama drama is: {np.dot(np.transpose(solution),np.array([[10],[1]]))}")