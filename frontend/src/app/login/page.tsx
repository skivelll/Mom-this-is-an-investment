import Image from "next/image";
import { LoginForm } from "@/features/auth/auth-forms";

export default function LoginPage() {
  return (
    <main className="grid min-h-screen place-items-center p-4">
      <div className="grid w-full max-w-5xl items-center gap-8 md:grid-cols-[1fr_420px]">
        <div>
          <Image
            src="/logo.png"
            alt="Мам, это инвестиция"
            width={440}
            height={440}
            priority
            className="mx-auto rounded-xl border-2 border-border bg-surface shadow-ink"
          />
        </div>
        <LoginForm />
      </div>
    </main>
  );
}
