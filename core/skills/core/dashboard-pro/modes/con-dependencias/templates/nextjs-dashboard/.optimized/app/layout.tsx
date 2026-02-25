import type {Metadata} from "next";import {Inter} from "next/font/google";import "./globals.css";import {ThemeProvider} from "@/components/theme-provider";const inter = Inter({subsets: ["latin"]});export const metadata: Metadata = {title: "{{project_title}}",description: "{{project_description}}",};export default function RootLayout({children,}: Readonly<{
  children: React.ReactNode;
}>) {return (<html lang="es" suppressHydrationWarning> <body className={inter.className}> <ThemeProvider
          attribute="class"
          defaultTheme="{{default_theme}}"
          enableSystem
          disableTransitionOnChange
        > {children} </ThemeProvider> </body> </html>);}