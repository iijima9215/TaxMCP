import Link from "next/link";

export default function Home() {
  return (
    <div className="font-sans grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start">
        <h1 className="text-4xl font-bold text-center">
          GPT-4o mini Chat App
        </h1>
        <p className="text-lg text-center text-gray-600">
          ChatGPTライクなインターフェースでGPT-4o miniと会話できます
        </p>

        <div className="flex gap-4 items-center flex-col sm:flex-row">
          <Link
            href="/chat"
            className="rounded-full border border-solid border-transparent transition-colors flex items-center justify-center bg-blue-500 text-white gap-2 hover:bg-blue-600 font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 sm:w-auto"
          >
            チャットを開始
          </Link>
        </div>
      </main>
      <footer className="row-start-3 flex gap-[24px] flex-wrap items-center justify-center">
        <p className="text-sm text-gray-500">
          Powered by GPT-4o mini & Next.js
        </p>
      </footer>
    </div>
  );
}
