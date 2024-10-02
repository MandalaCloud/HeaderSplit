# HeaderSplit: An Automated Tool for Splitting Header Files in C Projects

HeaderSplit is an automated tool for splitting header files.

It builds upon our previous research [Decomposing God Header File via Multi-View Graph Clustering](https://arxiv.org/abs/2406.16487) and is extended as a VS Code plugin. 
It not only suggests decomposition plans but also conducts the refactorings automatically. The example project is [filejail](https://github.com/netblue30/firejail), you can pick src/firejail/firejail.h as the split file to evaluate the method.

## Requirements

* python 3.9
* node.js 16.x

python packages and recommended versions:
* tree-sitter               0.22.3                   
* tree-sitter-c             0.21.4 
* numpy                     1.26.4                 
* scikit-learn              1.0.2            
* nltk                      3.7
* networkx                  2.8.4
* torch                     2.0.0
* openai                    1.35.1

## Extension Settings

This extension contributes the following settings:

* `newfileName.UseGPT`: Whether to use LLM to name the new file
* `newfileName.key`: Your own API key for LLM.
* `newfileName.proxy`: The hostname and port number of the proxy server used to access the GPT service.
* `newfileName.model`: The model you want to use.

## Usage

### Source Code

1. Clone and open this project in your VS Code.
2. Run `npm install` in the root path of this project.
3. `Run`-`Start Debugging`.

### VS Code Plugin

We have integrated the requirements into the plugin, so there is no need to configure them locally.

1. Clone HeaderSplit.vsix in your computer.
2. Open the Extensions view and click on the '...' (More Actions) button at the top-right corner, select Install from VSIX... from the dropdown menu and open HeaderSplit.vsix.
 ![Step1](./source_code/intro.png)
3. After installation, right-click on a specified header file, once you select HeaderSplit, the process of splitting the header file begins. 
