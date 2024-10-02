import os
import sys
from tree_sitter import Language, Parser
import tree_sitter_c as tsc
import pickle

from code_element_graph_construction.graph_schema import CodeElement, HeaderFile
from code_element_graph_construction.utils import *
from code_element_graph_construction.weighted_edge import *


# given a file path, return a HeaderFile object
def construct_header_file(file_path, c_parser):
    code_content = read_content(file_path)
    # print(file_path)
    
    header_file = HeaderFile(file_path)
    header_file.code_content = code_content

    tree = c_parser.parse(bytes(''.join(code_content),"utf8"))
    cursor = tree.walk()

    def dfs(node, depth):
        # print(node.type)
        # print(node.start_point, node.end_point)

        # this file --include--> other header file
        if node.type == "preproc_include":
            header_file.include.add(get_include_name(node, code_content))
            return

        '''
        parsing code elements and their dependencies
        '''
    
        if node.type == "preproc_def" or node.type == "preproc_function_def":
            code_element = CodeElement(node)
            code_element.reference = get_reference(node, code_content, header_file)
            code_element.name = get_name(node.child_by_field_name("name"), code_content)
            # print(code_element.name)
            code_element.new_name.append(code_element.name)
            header_file.add_code_element(code_element)
            return
            
        if node.type == "type_definition":
            root_node = node

            if node.child_by_field_name("declarator") is not None:
                node = node.child_by_field_name("declarator")
                def inner_dfs(node):
                        if node.type == "type_identifier":
                            return node
                        if node.child_count == 0:
                            return None
                        else:
                            for child in node.children:
                                result = inner_dfs(child)
                                if result is not None:
                                    return result
                # in case that return type is not primitive type / point declarator
                if node.type == "pointer_declarator":
                    code_element = CodeElement(node.parent)
                    code_element.reference = get_reference(node.parent, code_content, header_file)
                    while node.type == "pointer_declarator":
                        node = node.child_by_field_name("declarator")
                    if node.type == "function_declarator":
                        node = inner_dfs(node)
                        if node == None:
                            print(file_path, code_element.start, code_element.end)
                            return
                        code_element.name = get_name(node, code_content)
                        code_element.new_name.append(code_element.name)
                        header_file.add_code_element(code_element)
                        return
                    elif node.type == "type_identifier":
                        code_element.name = get_name(node, code_content)
                        code_element.new_name.append(code_element.name)
                        header_file.add_code_element(code_element)
                    else:
                        print("type_definition->pointer_declarator:", file_path, code_element.start, code_element.end)
                    
                if node.type == "function_declarator":
                    code_element = CodeElement(node.parent)
                    code_element.reference = get_reference(node.parent, code_content, header_file)
                    node = inner_dfs(node)
                    if node == None:
                        print(file_path, code_element.start, code_element.end)
                        return
                    code_element.name = get_name(node, code_content)
                    # print(code_element.name)
                    code_element.new_name.append(code_element.name)
                    header_file.add_code_element(code_element)
                    return
                if node.type == "type_identifier":
                    code_element = CodeElement(node.parent)
                    code_element.reference = get_reference(node.parent, code_content, header_file)
                    code_element.name = get_name(node, code_content)
                    # print(code_element.name)
                    code_element.new_name.append(code_element.name)
                    header_file.add_code_element(code_element)
                    return

            node = root_node

            if node.child_by_field_name("type") is None:
                return
            
            node = node.child_by_field_name("type")
            
            if node.type == "enum_specifier":
                code_element = CodeElement(node.parent)
                code_element.reference = get_reference(node.parent, code_content, header_file)
                code_element.name = get_name(node.next_sibling, code_content)
                if node.child_by_field_name("name") is not None:
                    alias_name = get_name(node.child_by_field_name("name"), code_content)
                    if not alias_name == code_element.name:
                        code_element.new_name.append(alias_name)
                code_element.new_name.append(code_element.name)
                if node.child_by_field_name("body") is not None:
                    for enumerator in node.child_by_field_name("body").children:
                        if enumerator.type == "enumerator":
                            code_element.new_name.append(get_name(enumerator.child_by_field_name("name"), code_content))
                header_file.add_code_element(code_element)
                return 

            if node.type == "struct_specifier" or node.type == "union_specifier":
                code_element = CodeElement(node.parent)
                code_element.reference = get_reference(node.parent, code_content, header_file)
                code_element.name = get_name(node.next_sibling, code_content)
                if node.child_by_field_name("name") is not None:
                    alias_name = get_name(node.child_by_field_name("name"), code_content)
                    if not alias_name == code_element.name:
                        code_element.new_name.append(alias_name)
                code_element.new_name.append(code_element.name)
                header_file.add_code_element(code_element)
                return
            
            if node.type == "type_identifier" or node.type == "primitive_type":
                code_element = CodeElement(node.parent)
                code_element.reference = get_reference(node.parent, code_content, header_file)
                node = node.next_sibling
                if node.type == "type_identifier":
                    code_element.name = get_name(node, code_content)
                else: #node.type == "function_declarator":
                    def inner_dfs(node):
                        if node.type == "type_identifier":
                            return node
                        if node.child_count == 0:
                            return None
                        else:
                            for child in node.children:
                                result = inner_dfs(child)
                                if result is not None:
                                    return result
                    node = inner_dfs(node)
                    if node == None:
                        print(file_path, code_element.start, code_element.end)
                        return
                    code_element.name = get_name(node, code_content)
                code_element.new_name.append(code_element.name)
                header_file.add_code_element(code_element)
                return

        if (node.type == "struct_specifier" or node.type == "union_specifier" or node.type == "enum_specifier") and (node.next_sibling is not None and node.next_sibling.type == ";"):
            code_element = CodeElement(node)
            code_element.reference = get_reference(node, code_content, header_file)
            if node.child_by_field_name("name") is not None:
                code_element.name = get_name(node.child_by_field_name("name"), code_content)
            else:
                code_element.name = header_file.file_path.split("\\")[-1].split(".")[0] + "_" + str(code_element.start[0]) + "_" + str(code_element.start[1])
            code_element.new_name.append(code_element.name)
            if node.type == "enum_specifier" and node.child_by_field_name("body") is not None:
                for enumerator in node.child_by_field_name("body").children:
                    if enumerator.type == "enumerator":
                        code_element.new_name.append(get_name(enumerator.child_by_field_name("name"), code_content))
            header_file.add_code_element(code_element)
            return
            
        if node.type == "declaration" and node.parent.type != "compound_statement":
            if node.child_by_field_name("declarator") is None:
                return
            node = node.child_by_field_name("declarator")
            if node.type == "array_declarator":
                code_element = CodeElement(node.parent)
                new_node = node.child_by_field_name("declarator")
                # multi-dimensional array
                try:
                    while new_node.type != "identifier":
                        new_node = new_node.child_by_field_name("declarator")
                except:
                    return
                code_element.name = get_name(new_node, code_content)
                code_element.new_name.append(code_element.name)
                code_element.reference = get_reference(node.parent, code_content, header_file)
                header_file.add_code_element(code_element)

                return

            if node.type == "pointer_declarator":
                node = node.child_by_field_name("declarator")
                # return type is pointer
                if node.type == "function_declarator":
                    code_element = CodeElement(node.parent.parent)
                    new_node = node
                    while new_node.child_by_field_name("declarator") is not None or new_node.type == "parenthesized_declarator":
                        # 0 (; 1 ?; 2 )
                        if new_node.type == "parenthesized_declarator":
                            new_node = new_node.children[1]
                        else:
                            new_node = new_node.child_by_field_name("declarator")
                    code_element.name = get_name(new_node, code_content)
                    code_element.new_name.append(code_element.name)
                    code_element.reference = get_reference(node.parent.parent, code_content, header_file)
                    header_file.add_code_element(code_element)
                    return

            if node.type == "init_declarator":
                if node.child_by_field_name("declarator") is None:
                    return
                code_element = CodeElement(node.parent)
                if node.child_by_field_name("declarator").type == "array_declarator":
                    code_element.name = get_name(node.child_by_field_name("declarator").child_by_field_name("declarator"), code_content)
                else:
                    code_element.name = get_name(node.child_by_field_name("declarator"), code_content)
                code_element.new_name.append(code_element.name)
                code_element.reference = get_reference(node.parent, code_content, header_file)
                header_file.add_code_element(code_element)
                return
                
            if node.type == "function_declarator":
                code_element = CodeElement(node.parent)
                new_node = node.child_by_field_name("declarator")
                if new_node.type == "function_declarator":
                    try:
                        new_node = new_node.children[1].children[2].children[0]
                    except:
                        # print(file_path, new_node.start_point)
                        return
                elif new_node.type == "parenthesized_declarator":
                    new_node = new_node.children[1]
                    while new_node.child_by_field_name("declarator") is not None:
                        new_node = new_node.child_by_field_name("declarator")
                code_element.name = get_name(new_node, code_content)
                code_element.new_name.append(code_element.name)
                code_element.reference = get_reference(node.parent, code_content, header_file)
                header_file.add_code_element(code_element)
                return
            
            # do not support such format: extern macro type identifier
            if node.type == "identifier":
                try:
                    if node.parent.children[-1].type == ";" and node.parent.children[-1].is_missing:
                        # print(header_file.file_path, node.parent.start_point)
                        return
                except:
                    print(header_file.file_path, node.parent.start_point)
                code_element = CodeElement(node.parent)
                code_element.name = get_name(node, code_content)
                code_element.new_name.append(code_element.name)
                code_element.reference = get_reference(node.parent, code_content, header_file)
                header_file.add_code_element(code_element)
                return

            return
            
        if node.type == "function_definition":
            if node.child_by_field_name("declarator") is None:
                return
            node = node.child_by_field_name("declarator")

            if node.type == "function_declarator":
                code_element = CodeElement(node.parent)
                code_element.reference = get_reference(node.parent, code_content, header_file)
                code_element.name = get_name(node.child_by_field_name("declarator"), code_content)
                code_element.new_name.append(code_element.name)
                header_file.add_code_element(code_element)
                return
            
            if node.type == "pointer_declarator":
                node = node.child_by_field_name("declarator")
                # return type is pointer
                if node.type == "function_declarator":
                    code_element = CodeElement(node.parent.parent)
                    new_node = node
                    while new_node.child_by_field_name("declarator") is not None or new_node.type == "parenthesized_declarator":
                        # 0 (; 1 ?; 2 )
                        if new_node.type == "parenthesized_declarator":
                            new_node = new_node.children[1]
                        else:
                            new_node = new_node.child_by_field_name("declarator")
                    code_element.name = get_name(new_node, code_content)
                    code_element.new_name.append(code_element.name)
                    code_element.reference = get_reference(node.parent.parent, code_content, header_file)
                    header_file.add_code_element(code_element)
                    return

            if node.type == "parenthesized_declarator":
                code_element = CodeElement(node.parent)
                code_element.reference = get_reference(node.parent, code_content, header_file)
                code_element.name = get_name(node.prev_sibling, code_content)
                # print(code_element.name)
                code_element.new_name.append(code_element.name)
                header_file.add_code_element(code_element)
                return
        
        # tree sitter bug
        if node.type == "ERROR":
            for child in node.children:
                if child.type == "function_declarator":
                    code_element = CodeElement(node)
                    code_element.type = "declaration"
                    code_element.reference = get_reference(node, code_content, header_file)
                    code_element.name = get_name(child.child_by_field_name("declarator"), code_content)
                    code_element.new_name.append(code_element.name)
                    header_file.add_code_element(code_element)
                    return
        
        if node.type == "expression_statement":
            return
        
        if node.child_count == 0:
            return
        else:
            if depth > 990:
                return
            for child in node.children:
                dfs(child, depth+1)

    dfs(cursor.node, 0)

    return header_file



# given a project, return a list of HeaderFile objects
def construct_reference_graph(project_dir, parser, target_header_file_path):

    header_files = dict()

    # recursive traverse the project directory
    def traverse(path):
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isdir(file_path):
                traverse(file_path)
            else:
                if file_path.endswith(".h"):
                    header_file = construct_header_file(file_path, parser)
                    header_files.update({file_path: header_file})
    

    # recursive traverse the project directory
    def traverse_c(path):
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isdir(file_path):
                traverse_c(file_path)
            else:
                if file_path.endswith(".c"):
                    get_referenced_by(file_path, parser, header_files)


    print("constructing code element graph for " + project_dir)
    # parse code elements and intra-file relationships
    print("step 1 of 5: parsing code elements and intra-file relationships")
    traverse(project_dir)

    # parse inter-file be-referenced relationships 
    print("step 2 of 5: parsing direct inter-file be-referenced relationships between c file and h file")
    traverse_c(project_dir)

    # parse inter-file referenced relationships
    print("step 3 of 5: parsing direct inter-file referenced relationships among h files")
    get_include(header_files, parser)  

    print("step 4 of 5: looking for all downstream files and direct dependency relationships")
    header_file = header_files[os.path.join(project_dir, target_header_file_path)]

    # downstream files
    all_included_by = get_all_include_by(header_file, header_files)
    # direct dependency by downstream files
    for file in (all_included_by - header_file.included_by):
        if file.endswith(".c"):
            get_referenced_by_for_target_h_file(file, header_file, parser)
        else:
            # record downstream relation but not upstream relation
            get_include_for_target_h_file(header_files[file], header_file, parser)
    header_file.included_by = all_included_by

    print("step 5 of 5: c --indirect use--> code element")
    for code_element in header_file.code_elements:
        indirect_reference_by = get_indirect_reference_by(code_element)
        code_element.referenced_by.update(indirect_reference_by)

    return header_files


def save_header_files(project, header_files):
    with open(project + ".pkl", "wb") as f:
        pickle.dump(header_files, f)


def load_header_files_from_pickle(project):
    with open(project + ".pkl", "rb") as f:
        header_files = pickle.load(f)
    return header_files


def construct_pkl_graph(project_dir, target_header_file_path):

    C_LANGUAGE = Language(tsc.language())
    parser = Parser(C_LANGUAGE)

    project = project_dir.split(os.sep)[-1]

    header_files = construct_reference_graph(project_dir, parser, target_header_file_path)
    save_header_files(project, header_files)
    return header_files


def get_code_element_graph(project_dir, target_header_file_path):
    try:
        header_files = load_header_files_from_pickle(project_dir.split(os.sep)[-1])
        print("Code element graph loaded successfully.")
        return header_files
    except:
        print("Constructing code element graph for the first time. This may take a while.")
        return construct_pkl_graph(project_dir, target_header_file_path)



