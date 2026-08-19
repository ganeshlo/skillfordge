export function MarkdownPreview({ content }: { content: string }) {
  return (
    <div className="prose-note space-y-2 text-sm leading-7 text-slate-700 dark:text-slate-200">
      {content.split("\n").map((raw, index) => {
        const line = raw.trim();
        if (!line) return <div key={index} className="h-2" />;
        if (line.startsWith("### "))
          return (
            <h4 key={index} className="pt-2 text-base font-black">
              {line.slice(4)}
            </h4>
          );
        if (line.startsWith("## "))
          return (
            <h3 key={index} className="pt-3 text-xl font-black">
              {line.slice(3)}
            </h3>
          );
        if (line.startsWith("# "))
          return (
            <h2
              key={index}
              className="text-2xl font-black tracking-tight text-slate-950 dark:text-white"
            >
              {line.slice(2)}
            </h2>
          );
        if (/^[-*] \[[ xX]\] /.test(line))
          return (
            <p key={index} className="flex gap-2">
              <input
                type="checkbox"
                readOnly
                checked={line[3].toLowerCase() === "x"}
              />
              {line.slice(6)}
            </p>
          );
        if (line.startsWith("- ") || line.startsWith("* "))
          return (
            <p
              key={index}
              className="pl-5 before:-ml-4 before:mr-2 before:text-indigo-500 before:content-['•']"
            >
              {line.slice(2)}
            </p>
          );
        if (line.startsWith("```"))
          return (
            <code
              key={index}
              className="block rounded-lg bg-slate-950 px-3 py-2 font-mono text-xs text-slate-100"
            >
              {line.slice(3)}
            </code>
          );
        return <p key={index}>{line}</p>;
      })}
    </div>
  );
}
