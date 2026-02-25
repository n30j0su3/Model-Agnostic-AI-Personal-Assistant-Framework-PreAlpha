import{type ClassValue,clsx}from"clsx";
import{twMerge}from"tailwind-merge";

export function cn(...inputs:ClassValue[]){return twMerge(clsx(inputs));}

export const formatCurrency=(v:number)=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD"}).format(v);
export const formatNumber=(v:number)=>new Intl.NumberFormat("en-US").format(v);
export const formatPercentage=(v:number)=>`${v>=0?"+":""}${v.toFixed(2)}%`;

export function convertToRgba({color,opacity}:{color:string;opacity:number}):string{
if(color.startsWith("#")){
const r=parseInt(color.slice(1,3),16),g=parseInt(color.slice(3,5),16),b=parseInt(color.slice(5,7),16);
return`rgba(${r},${g},${b},${opacity})`;
}
if(color.startsWith("rgb")){
const v=color.match(/\d+/g);
if(v)return`rgba(${v[0]},${v[1]},${v[2]},${opacity})`;
}
return color;
}
