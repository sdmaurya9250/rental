# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.

[//]: # (backend/)

[//]: # (├── app/)

[//]: # (│   ├── __init__.py)

[//]: # (│   ├── main.py                 ← FastAPI app + Cloudflare entrypoint)

[//]: # (│   ├── models/)

[//]: # (│   │   ├── __init__.py)

[//]: # (│   │   └── user.py             ← Pydantic models)

[//]: # (│   ├── routes/)

[//]: # (│   │   ├── __init__.py)

[//]: # (│   │   ├── auth.py             ← Register + Login routes)

[//]: # (│   │   └── health.py)

[//]: # (│   ├── services/)

[//]: # (│   │   ├── __init__.py)

[//]: # (│   │   └── auth_service.py     ← Business logic)

[//]: # (│   └── utils/)

[//]: # (│       ├── __init__.py)

[//]: # (│       └── security.py         ← Password hashing etc.)

[//]: # (├── wrangler.toml)

[//]: # (├── pyproject.toml)

[//]: # (└── README.md)
