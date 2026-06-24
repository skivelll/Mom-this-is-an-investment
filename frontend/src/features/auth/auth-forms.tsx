"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useLogin, useRegister } from "@/shared/auth/use-auth";
import { ErrorMessage, FieldError, Panel } from "@/shared/components/ui";

const loginSchema = z.object({
  email: z.string().email("Введите email."),
  password: z.string().min(8, "Минимум 8 символов."),
});

const registerSchema = loginSchema.extend({
  username: z.string().min(2, "Минимум 2 символа.").max(100),
});

export function LoginForm() {
  const router = useRouter();
  const search = useSearchParams();
  const login = useLogin();
  const form = useForm<z.infer<typeof loginSchema>>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "user@example.com", password: "password123" },
  });

  return (
    <Panel className="w-full max-w-md">
      <h1 className="font-display text-4xl uppercase">Вход</h1>
      <p className="mt-2 text-muted">JWT авторизация. Dev-пароль для seed-пользователей: password123.</p>
      <form
        className="mt-6 grid gap-4"
        onSubmit={form.handleSubmit(async (values) => {
          await login.mutateAsync(values);
          router.push(search.get("next") ?? "/dashboard");
        })}
      >
        <label>
          <span className="label">Email</span>
          <input className="ink-input" {...form.register("email")} />
          <FieldError message={form.formState.errors.email?.message} />
        </label>
        <label>
          <span className="label">Пароль</span>
          <input className="ink-input" type="password" {...form.register("password")} />
          <FieldError message={form.formState.errors.password?.message} />
        </label>
        {login.error ? <ErrorMessage error={login.error} /> : null}
        <button className="ink-button ink-button-accent" disabled={login.isPending}>
          {login.isPending ? "Входим..." : "Войти"}
        </button>
      </form>
      <Link className="mt-4 inline-block font-bold text-accent" href="/register">
        Нет аккаунта? Зарегистрироваться
      </Link>
    </Panel>
  );
}

export function RegisterForm() {
  const router = useRouter();
  const registerUser = useRegister();
  const form = useForm<z.infer<typeof registerSchema>>({
    resolver: zodResolver(registerSchema),
    defaultValues: { username: "", email: "", password: "" },
  });

  return (
    <Panel className="w-full max-w-md">
      <h1 className="font-display text-4xl uppercase">Регистрация</h1>
      <p className="mt-2 text-muted">Создаём обычного пользователя. Роли модераторов задаются seed-данными.</p>
      <form
        className="mt-6 grid gap-4"
        onSubmit={form.handleSubmit(async (values) => {
          await registerUser.mutateAsync(values);
          router.push("/login");
        })}
      >
        <label>
          <span className="label">Ник</span>
          <input className="ink-input" {...form.register("username")} />
          <FieldError message={form.formState.errors.username?.message} />
        </label>
        <label>
          <span className="label">Email</span>
          <input className="ink-input" {...form.register("email")} />
          <FieldError message={form.formState.errors.email?.message} />
        </label>
        <label>
          <span className="label">Пароль</span>
          <input className="ink-input" type="password" {...form.register("password")} />
          <FieldError message={form.formState.errors.password?.message} />
        </label>
        {registerUser.error ? <ErrorMessage error={registerUser.error} /> : null}
        <button className="ink-button ink-button-accent" disabled={registerUser.isPending}>
          {registerUser.isPending ? "Создаём..." : "Создать аккаунт"}
        </button>
      </form>
      <Link className="mt-4 inline-block font-bold text-accent" href="/login">
        Уже есть аккаунт? Войти
      </Link>
    </Panel>
  );
}
