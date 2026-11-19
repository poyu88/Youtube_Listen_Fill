import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import type { Token } from "../types";

interface BlankFillProps {
  tokens: Token[];
  segmentKey: string | number;
}

/**
 * 挖空聽打輸入區：字母自動跳格、提示、檢查答案、翻譯佔位。
 */
export default function BlankFill({ tokens, segmentKey }: BlankFillProps) {
  const letterIndexes = useMemo(
    () =>
      tokens
        .map((token, index) => (token.type === "letter" ? index : -1))
        .filter((index) => index >= 0),
    [tokens],
  );

  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [focusPos, setFocusPos] = useState(0);
  const [checked, setChecked] = useState(false);
  const [showTranslation, setShowTranslation] = useState(false);
  const inputRefs = useRef<Array<HTMLInputElement | null>>([]);

  useEffect(() => {
    setAnswers({});
    setFocusPos(0);
    setChecked(false);
    setShowTranslation(false);
    inputRefs.current = [];
  }, [segmentKey]);

  useEffect(() => {
    const tokenIndex = letterIndexes[focusPos];
    if (tokenIndex == null) return;
    const el = inputRefs.current[tokenIndex];
    el?.focus();
  }, [focusPos, letterIndexes, segmentKey]);

  function handleLetterInput(tokenIndex: number, letterPos: number, raw: string) {
    const char = raw.slice(-1);
    if (!char || !/^[a-zA-Z]$/.test(char)) {
      if (raw === "") {
        setAnswers((prev) => {
          const next = { ...prev };
          delete next[tokenIndex];
          return next;
        });
      }
      return;
    }

    setAnswers((prev) => ({ ...prev, [tokenIndex]: char }));
    setChecked(false);
    if (letterPos < letterIndexes.length - 1) {
      setFocusPos(letterPos + 1);
    }
  }

  function handleKeyDown(letterPos: number, event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Backspace") {
      const tokenIndex = letterIndexes[letterPos];
      if (tokenIndex == null) return;
      if (answers[tokenIndex]) {
        setAnswers((prev) => {
          const next = { ...prev };
          delete next[tokenIndex];
          return next;
        });
      } else if (letterPos > 0) {
        const prevIndex = letterIndexes[letterPos - 1];
        setAnswers((prev) => {
          const next = { ...prev };
          if (prevIndex != null) delete next[prevIndex];
          return next;
        });
        setFocusPos(letterPos - 1);
      }
      event.preventDefault();
    } else if (event.key === "ArrowLeft" && letterPos > 0) {
      setFocusPos(letterPos - 1);
      event.preventDefault();
    } else if (event.key === "ArrowRight" && letterPos < letterIndexes.length - 1) {
      setFocusPos(letterPos + 1);
      event.preventDefault();
    }
  }

  function handleHint() {
    const nextEmptyPos = letterIndexes.findIndex((tokenIndex) => !answers[tokenIndex]);
    const targetPos = nextEmptyPos >= 0 ? nextEmptyPos : letterIndexes.length - 1;
    const tokenIndex = letterIndexes[targetPos];
    if (tokenIndex == null) return;
    const expected = tokens[tokenIndex]?.value ?? "";
    setAnswers((prev) => ({ ...prev, [tokenIndex]: expected }));
    setChecked(false);
    if (targetPos < letterIndexes.length - 1) {
      setFocusPos(targetPos + 1);
    } else {
      setFocusPos(targetPos);
    }
  }

  function handleCheck() {
    setChecked(true);
  }

  function handleTranslation() {
    setShowTranslation((prev) => !prev);
  }

  let letterPosCounter = -1;

  return (
    <div className="blank-fill-panel">
      <div className="blank-fill-main">
        <h3>填空練習區</h3>
        <div className="blank-row" aria-label="挖空輸入">
          {tokens.map((token, index) => {
            if (token.type === "space") {
              return <span key={index} className="blank-space" />;
            }
            if (token.type === "punct") {
              return (
                <span key={index} className="blank-punct">
                  {token.value}
                </span>
              );
            }

            letterPosCounter += 1;
            const letterPos = letterPosCounter;
            const value = answers[index] ?? "";
            const expected = token.value;
            let statusClass = "";
            if (checked) {
              statusClass =
                value.toLowerCase() === expected.toLowerCase() ? "correct" : "wrong";
            }

            return (
              <input
                key={index}
                ref={(el) => {
                  inputRefs.current[index] = el;
                }}
                className={`blank-letter ${statusClass}`}
                value={value}
                maxLength={1}
                autoComplete="off"
                spellCheck={false}
                aria-label={`字母 ${letterPos + 1}`}
                onChange={(e) => handleLetterInput(index, letterPos, e.target.value)}
                onFocus={() => setFocusPos(letterPos)}
                onKeyDown={(e) => handleKeyDown(letterPos, e)}
              />
            );
          })}
        </div>

        {checked && (
          <div className="answer-row" aria-label="正確答案">
            {tokens.map((token, index) => {
              if (token.type === "space") {
                return <span key={index} className="blank-space" />;
              }
              if (token.type === "punct") {
                return (
                  <span key={index} className="blank-punct answer-punct">
                    {token.value}
                  </span>
                );
              }
              const typed = answers[index] ?? "";
              const ok = typed.toLowerCase() === token.value.toLowerCase();
              return (
                <span key={index} className={`answer-letter ${ok ? "correct" : "wrong"}`}>
                  {token.value}
                </span>
              );
            })}
          </div>
        )}

        {showTranslation && (
          <p className="translation-placeholder">此版本尚無翻譯</p>
        )}
      </div>

      <div className="blank-actions">
        <button type="button" onClick={handleHint}>
          Give me a hint
        </button>
        <button type="button" onClick={handleCheck}>
          Check Answer
        </button>
        <button type="button" onClick={handleTranslation}>
          Show Translation
        </button>
      </div>
    </div>
  );
}
