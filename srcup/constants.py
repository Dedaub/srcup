def get_extra_config(use_ir: bool):
    return f"""
const patchIr = {str(use_ir).lower()};
    """ + """\n
function patch_compiler_object(obj) {
    if (!Object.keys(obj).includes('settings')) {
        obj.settings = {}
    }

    if (!Object.keys(obj).includes('outputSelection')){
        obj.settings.outputSelection = {}
    }
    if (!Object.keys(obj).includes("*")){
        obj.settings.outputSelection["*"] = {};
    }
    if (!Object.keys(obj).includes("*")){
        obj.settings.outputSelection["*"]["*"] = [];
    }

    const outputs = obj.settings.outputSelection["*"]["*"];
    if (!outputs.includes('evm.deployedBytecode.functionDebugData')){
        outputs.push('evm.deployedBytecode.functionDebugData');
    }
    if (!outputs.includes('evm.deployedBytecode.immutableReferences')){
        outputs.push('evm.deployedBytecode.immutableReferences');
    }

    if (patchIr){
        if (!outputs.includes('irOptimizedAst')){
            outputs.push('irOptimizedAst');
        }
    }
}

if (typeof module.exports == "undefined"){
    module.exports = {}
}


if (Object.keys(module.exports.default.solidity).includes('compilers')){
    module.exports.default.solidity.compilers.forEach((c) => patch_compiler_object(c));
} else {
    patch_compiler_object(module.exports.default.solidity)
}
"""
