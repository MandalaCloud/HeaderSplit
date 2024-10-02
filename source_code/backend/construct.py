# -*- coding:utf-8 -*-

import os
import sys
import time
import json

from code_element_graph_construction.graph_constructor import get_code_element_graph
from decomposition_plan_generation.plan_generation import decomposing_through_Louvain, plan_overview
from decomposition_plan_generation.circular_dependency_fixing.fixing import circular_dependency_fixing
from decomposition_plan_generation.utils import simplify_community_index
from refactoring_implementation.file_name_generation import generate_file_names

print("Enter construct.py")

def construct(project_dir,target_header_file_path,parts, useGPT, key, URL, model):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    basename = os.path.basename(target_header_file_path)

    if getattr(sys, 'frozen', False):
        # 如果是打包后的 exe 文件
        print("Running as a frozen executable.")
        actual_exe_path = os.path.realpath(sys.argv[0])
        application_path = os.path.dirname(actual_exe_path)
    else:
        # 如果是从源码运行
        print("Running from source code.")
        script_path = os.path.abspath(__file__)
        application_path = os.path.dirname(script_path)
        print("Application path (source):", application_path)

    try:
        output_json_path = os.path.join(application_path, f"{basename}_{parts}_{useGPT}.json")
        with open(output_json_path, 'r', encoding='utf-8') as json_file:
            return
    except:
        print("Generating plan for the first time. This may take a while.")
        
        if project_dir[-1] == '/' or project_dir[-1] == '\\':
            project_dir = project_dir[:-1]
        project_dir = os.path.normpath(project_dir)
        
        project_name = project_dir.split(os.sep)[-1]

        header_files = get_code_element_graph(project_dir,target_header_file_path)

        prefix = list(header_files.keys())[0]
        prefix = prefix[:prefix.find(project_name)]
        target_file = os.path.join(prefix, project_name, target_header_file_path)
        target_header_file = header_files[target_file]

        # for code_element in target_header_file.code_elements:
        #     print(code_element.name + '+' + code_element.type + ";") 
            
        community_index = decomposing_through_Louvain(parts, target_header_file)
        # community_index = decomposing_through_DuaLGR(parts, target_header_file)

        community_index = circular_dependency_fixing(target_header_file, community_index)
        print("original community index: ", max(community_index.values()))

        community_index = simplify_community_index(community_index)
        print("new community index: ", max(community_index.values()))

        file_names = generate_file_names(target_header_file, community_index, useGPT, key, URL, model)
        print(len(file_names), file_names)

        json_content = plan_overview(target_header_file, community_index, file_names)
        output_json_path = os.path.join(application_path, f"plan_overview_{basename}_{parts}_{useGPT}.json")
        with open(output_json_path, 'w') as json_file:
            json.dump(json_content, json_file)
        
        output_json_path = os.path.join(application_path, f"{basename}_{parts}_{useGPT}.json")
        with open(output_json_path, 'w') as json_file:
            json.dump(community_index, json_file)
        
        return 

if __name__ == "__main__":
    if len(sys.argv) != 8:
        print(len(sys.argv))
        print("Usage: python call.py <project_dir> <target_header_file_path> <parts>")
        sys.exit(1)
        
    project_dir = sys.argv[1]
    target_header_file_path = sys.argv[2]
    parts = int(sys.argv[3])  
    useGPT_str = sys.argv[4].lower()
    useGPT = False
    if useGPT_str == "true" or useGPT_str == "1":
        useGPT = True
    key = sys.argv[5]
    URL = sys.argv[6]
    model = sys.argv[7]
    
    construct(project_dir, target_header_file_path, parts, useGPT, key, URL, model)
