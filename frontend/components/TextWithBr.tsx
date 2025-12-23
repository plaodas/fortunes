// コンポーネント例
import React from "react";

export default function TextWithBr({ text }: { text: string }) {
    const lines = text.split("\n");
    return (
        <>
            {lines.map((line, i) => (
                <React.Fragment key={i}>
                    {line}
                    {i < lines.length - 1 && <br />}
                </React.Fragment>
            ))}
        </>
    );
}
