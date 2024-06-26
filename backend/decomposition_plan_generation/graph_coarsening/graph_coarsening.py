import numpy as np
from code_element_graph_construction.weighted_edge import *

def merge_blocks(blocks, r, c):
    if r > c:
        tmp = r
        r = c
        c= tmp
    blocks[r].extend(blocks[c])
    blocks.pop(c)
    return blocks

def merge_matrix(matrix, r, c):
    if r > c:
        tmp = r
        r = c
        c= tmp
    matrix[r, :] = np.maximum(matrix[r, :], matrix[c, :])
    matrix[:, r] = np.maximum(matrix[:, r], matrix[:, c])
    matrix = np.delete(matrix, c, axis=0)
    matrix = np.delete(matrix, c, axis=1)
    matrix[r, r] = 0
    return matrix

# step 1
def bundle_code_elements_by_dependency(header_file, threshold=0.9):
    blocks = []
    for i in range(len(header_file.code_elements)):
        blocks.append([i])

    dependency = normalized_dependency(header_file)
    sharing_attribute = shared_dependency(header_file)
    matrix = dependency
    i = 0
    while True:
        max_value = np.max(matrix)
        if max_value < threshold:
            break
        r, c = np.where(matrix == max_value)
        # merge r[0], c[0]
        blocks = merge_blocks(blocks, r[0], c[0])
        matrix = merge_matrix(matrix, r[0], c[0])

        i = i + 1
    return blocks


def bundled_matrix(matrix, blocks):
    remove_index = []
    for block in blocks:
        if len(block) == 1:
            continue
        matrix[block[0], :] = np.max(matrix[block], axis=0)
        matrix[:, block[0]] = np.max(matrix[:, block], axis=1)
        matrix[block[0], block[0]] = 0
        remove_index.extend(block[1:])
    matrix = np.delete(matrix, remove_index, axis=0)
    matrix = np.delete(matrix, remove_index, axis=1)
    return matrix



def graph_coarsening(target_header_file):

    np.set_printoptions(threshold=np.inf)

    # step 1: bundle several code elements according to dependency
    blocks = bundle_code_elements_by_dependency(target_header_file)

    # step 2: matrix for clustering
    adj0 = normalized_dependency(target_header_file)
    adj1 = shared_usage_for_file(target_header_file)
    # adj2 = semantic_similarity_for_file(target_header_file)
    adj2 = LSI_similarity_for_file(target_header_file)

    bundled_usage = bundled_matrix(adj1, blocks)
    bundled_semantic = bundled_matrix(adj2, blocks)

    return blocks, bundled_usage, bundled_semantic, adj0+adj1+adj2


