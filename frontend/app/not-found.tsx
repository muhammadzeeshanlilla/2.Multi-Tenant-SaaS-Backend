import Link from "next/link";
import { Compass } from "lucide-react";
import { Button } from "@/components/ui/button";
export default function NotFound() { return <main className="grid min-h-screen place-items-center bg-slate-50 p-4"><div className="max-w-md text-center"><span className="mx-auto grid size-14 place-items-center rounded-2xl bg-indigo-100 text-indigo-700"><Compass className="size-7" /></span><p className="mt-6 text-sm font-bold text-indigo-700">404</p><h1 className="mt-2 text-3xl font-bold text-slate-950">Page not found</h1><p className="mt-3 text-slate-500">The page may have moved or may not be available for your role.</p><Link href="/dashboard" className="mt-6 inline-block"><Button>Return to dashboard</Button></Link></div></main>; }
