"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
const path = require("path");
const fs = require("fs");
const childProcess = require('child_process');

async function waitForMessage(panel) {
    return new Promise((resolve) => {
        panel.webview.onDidReceiveMessage(message => {
            if (message.command === 'number') {
                let number = message.parts;
                console.log(`Choose plan: sub_file number - ${number}`);
                resolve(number);
            }
            else if (message.command === 'start') {
                console.log(`Start refactoring`);
                resolve(true);
            }
            else if (message.command === 'back') {
                console.log(`Go back to choose the number`);
                resolve(false);
            }
            else {
                let project = message.filepath;
                console.log(`Received data: project - ${project}`);
                resolve(project);
            }
        });
    });
}

async function executePythonScript(pythonFilePath, projectDir, filePath, parts, name, useGPT, key = "", URL = "", model = "") {
    let commandline;
    if (name === "Construct") commandline = `${pythonFilePath} ${projectDir} ${filePath} ${parts} ${useGPT} ${key} ${URL} ${model}`;
    else commandline = `${pythonFilePath} ${projectDir} ${filePath} ${parts} ${useGPT}`;

    return new Promise((resolve, reject) => {
        childProcess.exec(commandline, (error, stdout, stderr) => {
            if (error) {
                console.error(`${name}-error: ${error}`);
                vscode.window.showWarningMessage(`${name}-error: ${error}`);
                reject(error);
            } else {
                console.log(`${name}-stdout: ${stdout}`);
                vscode.window.showInformationMessage(`${name}-stdout: ${stdout}`);
                resolve();
            }
        });
    });
}

function activate(context) {
    console.log('Congratulations, your extension "file-decomposing" is now active!');
    context.subscriptions.push(vscode.commands.registerCommand('extension.file-decomposing', async (uri) => {
        vscode.window.showInformationMessage('Welcome to use the file decomposing tool!');
        const panel = vscode.window.createWebviewPanel('file-decomposing start', 'File Decomposing', vscode.ViewColumn.One, {
            enableScripts: true,
        });

        const htmlFilePath1 = path.join(context.extensionPath, 'frontend', 'welcome.html');
        panel.webview.html = fs.readFileSync(htmlFilePath1, 'utf-8');
        panel.webview.postMessage({ file: `${path.basename(uri.path)}` });

        const workspaceFolder = vscode.workspace.workspaceFolders;
        if (!workspaceFolder || workspaceFolder.length === 0) {
            vscode.window.showWarningMessage('No workspace folder is open.Please select your workspace and restart.');
            return;
        }

        const project = await waitForMessage(panel);
        let project_dir = path.join(workspaceFolder[0].uri.fsPath, `${project}`);
        project_dir = path.normalize(project_dir);
        let filePath = path.normalize(uri.path);
        filePath = filePath.startsWith("/") || filePath.startsWith("\\") ? filePath.slice(1) : filePath;
        filePath = path.relative(project_dir, filePath);

        const config = vscode.workspace.getConfiguration("newfileName");
        const useGPT = config.get("UseGPT");
        let key = config.get("key");
        if (key === "") key = "none";
        const URL = config.get("proxy");
        const model = config.get("Model");

        let start_refactor = false;
        let parts;
        while (!start_refactor) {
            const htmlFilePath2 = path.join(context.extensionPath, 'frontend', 'number.html');
            panel.webview.html = fs.readFileSync(htmlFilePath2, 'utf-8');
            parts = await waitForMessage(panel);

            try {
                let pythonFilePath = path.join(context.extensionPath, 'backend', 'construct.exe');
                await executePythonScript(pythonFilePath, project_dir, filePath, parts, 'Construct', useGPT, key, URL, model);
                console.log('Construct execution complete.');
            } catch (error) {
                console.log('Error occurred during construct execution.');
            }

            console.log("Finish constructing, begin visualization");
            const community_index = path.join(context.extensionPath, 'backend', `plan_overview_${path.basename(uri.path)}_${parts}_${useGPT}.json`);
            const jsonContent = fs.readFileSync(community_index, 'utf-8');
            const jsonData = JSON.parse(jsonContent);

            const htmlFilePath3 = path.join(context.extensionPath, 'frontend', 'overview.html');
            panel.webview.html = fs.readFileSync(htmlFilePath3, 'utf-8');
            panel.webview.postMessage(jsonData);
            start_refactor = await waitForMessage(panel);
        }

        try {
            let pythonFilePath = path.join(context.extensionPath, 'backend', 'refactor.exe');
            await executePythonScript(pythonFilePath, project_dir, filePath, parts, 'Refactor', useGPT);
            console.log('Refactor execution complete.');
        } catch (error) {
            console.log('Error occurred during refactor execution.');
        }

        const htmlFilePath4 = path.join(context.extensionPath, 'frontend', 'finish.html');
        panel.webview.html = fs.readFileSync(htmlFilePath4, 'utf-8');
    }));
}
exports.activate = activate;
function deactivate() { }
exports.deactivate = deactivate;