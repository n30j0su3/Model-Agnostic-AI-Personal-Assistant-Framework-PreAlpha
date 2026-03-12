"use client";
import{Moon,Sun}from"lucide-react";
import{useTheme}from"next-themes";
import{Button}from"@/components/ui/button";

export function ThemeToggle(){
const{theme,setTheme}=useTheme();
return(
<Button variant="outline"size="icon"onClick={()=>setTheme(theme==="dark"?"light":"dark")}className="relative">
<Sun className="h-[1.2rem]w-[1.2rem]rotate-0scale-100transition-alldark:-rotate-90dark:scale-0"/>
<Moon className="absoluteh-[1.2rem]w-[1.2rem]rotate-90scale-0transition-alldark:rotate-0dark:scale-100"/>
<span className="sr-only">Toggle theme</span>
</Button>
);
}
