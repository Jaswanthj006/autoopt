const vscode = require('vscode');
const path = require('path');
const { exec } = require('child_process');

function activate(context) {

    const disposable = vscode.workspace.onDidSaveTextDocument((document) => {
        const filePath = document.uri.fsPath;
        if (!filePath.endsWith('.py')) {
            return;
        }
        if (filePath.endsWith('_optimized.py')) {
            return;
        }

        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return;
        }

        const workspaceRoot = workspaceFolder.uri.fsPath;
        const backendDir = path.join(workspaceRoot, 'backend');
        const agentPath = path.join(backendDir, 'agent.py');

        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'AutoOpt running...',
            cancellable: false
        }, () => {
            return new Promise((resolve, reject) => {
                exec(`python3 "${agentPath}" "${filePath}"`, {
                    cwd: backendDir
                }, (error, stdout, stderr) => {
                    if (error) {
                        vscode.window.showErrorMessage(`AutoOpt failed: ${error.message}`);
                        reject(error);
                        return;
                    }
                    vscode.window.showInformationMessage('AutoOpt finished');
                    resolve();
                });
            });
        });
    });

    context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
