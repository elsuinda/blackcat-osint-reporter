# BLACKCAT — ficha de uso (categoría: Informes)

> Herramienta propia de Hercule. Estacion **local** para armar informes OSINT:
> organiza casos y hallazgos y genera informes **customizables por destinatario**
> (tecnico, gerencial, judicial, cliente…). Corre en tu maquina (`localhost`) y,
> si querés, puede abrir un servidor en la **red local** para que colegas
> contribuyan al informe. Encaja de lleno en la fase de **Documenta** de la
> metodología "células grises".

---

## Cómo se abre y se cierra

```bash
blackcat start            # servidor local (solo tu maquina) + abre el navegador
blackcat start --share    # ademas lo publica en la red local (con clave de sesion)
blackcat stop             # lo detiene
blackcat status           # estado
```

También está el acceso directo **BLACKCAT** en el menú de aplicaciones.
Por defecto escucha en `http://127.0.0.1:8733`.

---

## Qué hace

| Pieza | Para qué sirve |
|-------|-----------------|
| **Casos** | Cada investigacion, con su codigo (BC-AÑO-N), alcance y **base de autorizacion**. |
| **Hallazgos** | Cada dato/evidencia: categoria, fuente, URL, confianza (confirmado/probable/sin verificar), **sensibilidad** y hash SHA-256 de integridad. |
| **Perfiles de destinatario** | Definen **como** se arma el informe para cada publico: que secciones lleva, nivel de detalle y hasta que sensibilidad/confianza se incluye. Vienen 4 listos (Tecnico/Pericial, Ejecutivo/Gerencial, Judicial, Cliente) y podés crear los tuyos. |
| **Informes** | Exporta a **PDF, Word (DOCX), HTML o Markdown**, filtrando el contenido segun el perfil, con su hash de integridad. |

---

## El informe customizable (la idea central)

Un mismo caso puede entregarse de formas muy distintas según a quién va dirigido.
En lugar de reescribir, elegís el **perfil de destinatario** al exportar:

- **Tecnico / Pericial:** todo, con fuentes, hashes y metadatos.
- **Ejecutivo / Gerencial:** resumen y hallazgos clave, sin tecnicismos ni datos internos.
- **Judicial:** con base de autorizacion, fuentes y hashes, formato para presentar.
- **Cliente:** presentable, solo hallazgos confirmados/probables, sin datos sensibles.

Los hallazgos marcados como **sensibles/internos** se ocultan automaticamente en los
perfiles pensados para publico externo.

---

## Trabajo colaborativo en red local (opcional)

Con `blackcat start --share` la app queda accesible desde otras maquinas de la
**red local**. La consola te muestra la **URL** y una **clave de sesion** aleatoria:
compartilas solo con quien corresponda. Cada persona entra con su nombre, y todo lo
que carga queda en el **registro de actividad** (quién hizo qué). Sin `--share`, nada
sale de tu maquina.

---

## Límites y uso responsable

- Herramienta de **documentacion**, no de recoleccion automatica: los hallazgos los
  cargás vos a partir de tu trabajo OSINT.
- Cargá siempre la **base de autorizacion** del caso. El "ético" es la línea que no se cruza.
- Respetá la Ley 25.326 (AR) / RGPD (UE). No es para acoso ni doxxing.
- La clave del modo compartido protege el acceso en la LAN; no expongas el puerto a internet.

---

*Herramienta de Miguel, integrada en Hercule.
— El Suinda @v@  ·  les petites cellules grises*
