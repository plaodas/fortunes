// 改行をBRに変換するコンポーネント
import React from "react";

const HEADING = /^(#{1,6})\s+(.*)$/

export default function TextWithBr({ text }: { text: string }) {
    if (!text) return null
    const lines = text.split("\n");
    return (
        <>
            {lines.map((line, i) => {
                const heading = HEADING.exec(line.trim())
                if (heading) {
                    const Tag = `h${heading[1].length}` as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
                    return <Tag key={i}>{heading[2]}</Tag>
                }
                return (
                    <React.Fragment key={i}>
                        {line}
                        {i < lines.length - 1 && <br />}
                    </React.Fragment>
                )
            })}
        </>
    );
}
