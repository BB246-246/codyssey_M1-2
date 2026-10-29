// Vercel 빌드 스크립트: 정적 파일을 dist/로 복사하고, 환경변수로 config.js를 만든다.
// 순수 HTML은 브라우저에서 환경변수를 읽을 수 없기 때문에 빌드 시점에 값을 파일로 박아 넣는다.
import { cpSync, mkdirSync, readdirSync, rmSync, writeFileSync } from "node:fs";

const apiBaseUrl = (process.env.API_BASE_URL || "").trim().replace(/\/+$/, "");
if (!apiBaseUrl) {
  console.error("API_BASE_URL 환경변수가 없습니다. Vercel 프로젝트 설정 > Environment Variables에 추가하세요.");
  process.exit(1);
}

const FILES = ["index.html", "style.css", "app.js", "chart.js"];

// 폴더째 지우지 않고 내용만 비운다 (로컬에서 dist를 서빙 중이어도 빌드 가능)
mkdirSync("dist", { recursive: true });
for (const f of readdirSync("dist")) rmSync(`dist/${f}`, { recursive: true, force: true });
for (const f of FILES) cpSync(f, `dist/${f}`);

writeFileSync(
  "dist/config.js",
  `window.APP_CONFIG = ${JSON.stringify({ API_BASE_URL: apiBaseUrl })};\n`,
);
console.log(`dist/ 생성 완료 (API_BASE_URL=${apiBaseUrl})`);
