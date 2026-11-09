# Actualizador Suwayomi para GitHub Actions

Este repositorio ejecuta el actualizador **sin interfaz**, dentro de GitHub
Actions, y sube los PDFs nuevos directamente a Telegram.

No guarda PDFs en el repositorio: usa `work/`, que está ignorado por Git.

## Qué hace

1. Descarga `catalog.json` y `aliases.json`.
2. Levanta Suwayomi en el runner de GitHub.
3. Lee los paquetes del catálogo para saber qué capítulos ya existen.
4. Busca:
   - Huecos intermedios.
   - Capítulos nuevos después del último.
5. Busca en todas las fuentes ES/EN instaladas.
6. Si una fuente no cubre un hueco, consulta las demás.
7. Descarga y empaqueta:
   - 10 o más capítulos corridos → un PDF.
   - 5 a 9 corridos → paquetes de 5 y sueltos.
   - 4 o menos → capítulos sueltos.
   - Tramos no corridos → no se mezclan.
8. Sube cada PDF a Telegram y verifica su tamaño.
9. Borra el PDF local después de verificarlo.
10. Manda/edita un mensaje de progreso a `@Markosantonio` cada 10 segundos.

## Archivos

```text
actualizador_headless.py       Worker sin Flask
requirements.txt               Dependencias Python
.github/workflows/actualizador.yml
suwayomi/extensions/*.jar      Extensiones de Suwayomi
tools/export_session.py        Convierte la sesión local a StringSession
.env.example                   Variables de ejemplo
```

## Secrets necesarios

En GitHub:

```text
Settings → Secrets and variables → Actions → New repository secret
```

Agrega:

| Secret | Valor |
|---|---|
| `TELEGRAM_API_ID` | Tu API ID |
| `TELEGRAM_API_HASH` | Tu API Hash |
| `TELEGRAM_SESSION` | StringSession del usuario |
| `TELEGRAM_UPLOAD_CHAT` | `-1004473963265` |
| `PROGRESS_CHAT` | `@Markosantonio` |

Opcionales:

| Secret | Valor |
|---|---|
| `CATALOG_URL` | URL raw del `catalog.json` |
| `ALIASES_URL` | URL raw del `aliases.json` |

## Sacar la StringSession

En tu PC, con `funcional.py`, `todost.py` y `tarantino.py` cerrados:

```powershell
cd C:\ManhuasCatalog\github_actualizador
python .\tools\export_session.py
```

Copia el texto que imprime en el secret `TELEGRAM_SESSION`.

No subas ese texto al repositorio.

## Caption de los PDFs

El caption lleva el hashtag y el origen:

```text
#Nombre_De_La_Serie (Respaldo)
```

o:

```text
#Nombre_De_La_Serie (Principal)
```

Se decide según los géneros de `catalog.json`:

- Si contiene `Respaldo` → `(Respaldo)`.
- Si no → `(Principal)`.

## Ejecutar

En GitHub:

```text
Actions → Actualizador Suwayomi → Run workflow
```

También queda programado cada 6 horas.

## Probar sin subir todo

Puedes agregar temporalmente en el workflow:

```yaml
env:
  MAX_SERIES: "5"
```

Así solo procesa 5 series.

## Suwayomi

El workflow:

- Descarga el JAR más reciente de Suwayomi.
- Copia las extensiones incluidas a la carpeta de datos.
- Lo arranca en `127.0.0.1:4567`.
- Espera a que responda GraphQL.

Si una fuente no aparece, revisa el log de Suwayomi en la ejecución.

## Limitaciones de GitHub Actions

- Máximo 6 horas por trabajo.
- El disco se borra al terminar.
- Las IPs de GitHub pueden estar bloqueadas por algunas webs.
- No hay interfaz web.
- En repos públicos los minutos son gratis; en privados hay límite.

## Seguridad

Nunca subas:

- `.env`
- `*.session`
- `TELEGRAM_SESSION`
- PDFs descargados

El workflow no hace `git add`, `git commit` ni `git push`.

## Verificación

```text
py_compile actualizador_headless.py: OK
py_compile tools/export_session.py: OK
```
