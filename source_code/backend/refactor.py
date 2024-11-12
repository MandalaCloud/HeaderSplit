import os
import sys
import json

from code_element_graph_construction.graph_constructor import get_code_element_graph
from decomposition_plan_generation.plan_generation import plan_overview
from refactoring_implementation.refactoring_implementation import refactoring

print("Enter refactor.py")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python call.py <project_dir> <target_header_file_path> <parts>")
        sys.exit(1)
        
    project_dir = sys.argv[1]
    target_header_file_path = sys.argv[2]
    parts = int(sys.argv[3])  
    if project_dir[-1] == '/' or project_dir[-1] == '\\':
        project_dir = project_dir[:-1]
    project_dir = os.path.normpath(project_dir)
    useGPT_str = sys.argv[4].lower()
    useGPT = False
    if useGPT_str == "true" or useGPT_str == "1":
        useGPT = True

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    project_name = project_dir.split(os.sep)[-1]

    header_files = get_code_element_graph(project_dir, target_header_file_path)

    prefix = list(header_files.keys())[0]
    prefix = prefix[:prefix.find(project_name)]
    target_file = os.path.join(prefix, project_name, target_header_file_path)
    target_header_file = header_files[target_file]

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

    output_json_path = os.path.join(application_path, f"plan_overview_{basename}_{parts}_{useGPT}.json")
    with open(output_json_path, 'r', encoding='utf-8') as json_file:
        plan_overview = json.load(json_file)

    output_json_path = os.path.join(application_path, f"{basename}_{parts}_{useGPT}.json")
    with open(output_json_path, 'r', encoding='utf-8') as json_file:
        community_index = json.load(json_file)

    file_names = []
    partition_data = plan_overview.get('partition', {})
    for header_file, items in partition_data.items():
        file_names.append(header_file)
    print(len(file_names), file_names)

    refactoring(project_dir, target_header_file_path, target_header_file, community_index, file_names)