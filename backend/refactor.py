import os
import sys
import json
import shutil

from code_element_graph_construction.graph_constructor import get_code_element_graph
from decomposition_plan_generation.plan_generation import decomposing_through_DuaLGR, decomposing_through_Louvain, plan_overview
from refactoring_implementation.refactoring_implementation import refactoring

print("Enter refactor.py")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python call.py <project_dir> <target_header_file_path> <parts>")
        sys.exit(1)
        
    project_dir = sys.argv[1]
    target_header_file_path = sys.argv[2]
    parts = int(sys.argv[3])  
    if project_dir[-1] == '/' or project_dir[-1] == '\\':
        project_dir = project_dir[:-1]
    project_dir = os.path.normpath(project_dir)

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    project_name = project_dir.split(os.sep)[-1]

    header_files = get_code_element_graph(project_dir, target_header_file_path)

    prefix = list(header_files.keys())[0]
    prefix = prefix[:prefix.find(project_name)]
    target_file = os.path.join(prefix, project_name, target_header_file_path)
    target_header_file = header_files[target_file]

    basename = os.path.basename(target_header_file_path)
    output_json_path = f"../intermediate_data/plan_overview_{basename}_{parts}.json"
    with open(output_json_path, 'r', encoding='utf-8') as json_file:
        plan_overview = json.load(json_file)

    output_json_path = f"../intermediate_data/{basename}_{parts}.json"
    with open(output_json_path, 'r', encoding='utf-8') as json_file:
        community_index = json.load(json_file)

    file_names = []
    partition_data = plan_overview.get('partition', {})
    for header_file, items in partition_data.items():
        file_names.append(header_file)
    print(len(file_names), file_names)

    refactoring(project_dir, target_header_file_path, target_header_file, community_index, file_names)

    if os.path.exists('../intermediate_data/'):
        shutil.rmtree('../intermediate_data/')