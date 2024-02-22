extra_config = """\n
if (typeof module.exports == "undefined"){
    module.exports = {}
}
if (!Object.keys(module.exports).includes('solidity')){
    module.exports.solidity = {}
    module.exports.solidity.version = "0.8.23"
}
if (!Object.keys(module.exports.solidity).includes('settings')) {
    module.exports.solidity.settings = {}
}
if (!Object.keys(module.exports.solidity.settings).includes('outputSelection')){
    module.exports.solidity.settings.outputSelection = {}
}
if (!Object.keys(module.exports.solidity.settings.outputSelection).includes("*")){
    module.exports.solidity.settings.outputSelection["*"] = {};
}
if (!Object.keys(module.exports.solidity.settings.outputSelection["*"]).includes("*")){
    module.exports.solidity.settings.outputSelection["*"]["*"] = [];
}

outputs = module.exports.solidity.settings.outputSelection["*"]["*"];
if (!outputs.includes('evm.deployedBytecode.functionDebugData')){
    outputs.push('evm.deployedBytecode.functionDebugData');
}
if (!outputs.includes('evm.deployedBytecode.immutableReferences')){
    outputs.push('evm.deployedBytecode.immutableReferences');
}
"""

ir_ast_config = """\n
if (!outputs.includes('irOptimizedAst')){
    outputs.push('irOptimizedAst');
}
"""
