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
        if (!outputs.includes('irOptimized')){
            outputs.push('irOptimized');
        }
    }
}

if (typeof module.exports == "undefined"){
    module.exports = {}
}

const base = module.exports.default ?? module.exports;

if (typeof base.solidity === "string" || base.solidity instanceof String) {
    base.solidity = {version: base.solidity}
}

if (Object.keys(base.solidity).includes('compilers')){
    base.solidity.compilers.forEach((c) => patch_compiler_object(c));
} else {
    patch_compiler_object(base.solidity)
}
"""
