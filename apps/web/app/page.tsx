import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-8">Sport SaaS</h1>
      <div className="flex gap-4">
        <Link href="/login" className="px-4 py-2 bg-blue-500 text-white rounded">Login</Link>
        <Link href="/register" className="px-4 py-2 bg-gray-500 text-white rounded">Register</Link>
        <Link href="/dashboard" className="px-4 py-2 bg-black text-white rounded">Dashboard</Link>
      </div>
    </main>
  );
}
