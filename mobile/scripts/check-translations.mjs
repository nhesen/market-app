import{readFileSync}from"node:fs";import{resolve}from"node:path";
const extract=file=>new Set([...readFileSync(resolve(file),"utf8").matchAll(/(?:^|[,{])\s*([A-Za-z][A-Za-z0-9_]*)\s*:/gm)].map(match=>match[1]));
const az=extract("locales/az.ts"),en=extract("locales/en.ts"),missingEn=[...az].filter(key=>!en.has(key)),missingAz=[...en].filter(key=>!az.has(key));
if(missingEn.length||missingAz.length){console.error("Translation integrity failed",{missingEn,missingAz});process.exit(1)}
console.log(`Translation integrity passed: ${az.size} AZ keys / ${en.size} EN keys`);
