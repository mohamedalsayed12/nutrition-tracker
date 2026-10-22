import { afterEach, describe, expect, it, vi } from "vitest"
import { ApiError, fieldErrors, request } from "./client.ts"

const tokenKey = "nutrition.access_token"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } })
}

afterEach(() => {
  vi.unstubAllGlobals()
  localStorage.clear()
})

describe("request", () => {
  it("maps error and validation details", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse(400, {
      error: "Invalid request.",
      details: [{ loc: ["body", "age"], msg: "Value error, Age must be from 18 to 100.", type: "value_error" }],
    })))
    const error = await request("/goals/nutrition", { method: "PUT", body: {} }).catch((caught: unknown) => caught)
    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).message).toBe("Invalid request.")
    expect(fieldErrors(error)).toEqual({ age: "Age must be from 18 to 100." })
  })

  it("reads a JWT msg and clears the token on 401", async () => {
    localStorage.setItem(tokenKey, "secret")
    const assign = vi.fn()
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse(401, { msg: "Not enough segments" })))
    vi.spyOn(window.location, "assign").mockImplementation(assign)
    const error = await request("/users/me").catch((caught: unknown) => caught)
    expect(error).toMatchObject({ status: 401, message: "Not enough segments" })
    expect(localStorage.getItem(tokenKey)).toBeNull()
    expect(assign).toHaveBeenCalledWith("/login")
  })

  it("leaves the token in place when login itself is rejected", async () => {
    localStorage.setItem(tokenKey, "secret")
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse(401, { error: "Invalid email or password." })))
    const error = await request("/auth/login", { method: "POST", body: {}, auth: false }).catch((caught: unknown) => caught)
    expect(error).toMatchObject({ status: 401, message: "Invalid email or password." })
    expect(localStorage.getItem(tokenKey)).toBe("secret")
  })
})
