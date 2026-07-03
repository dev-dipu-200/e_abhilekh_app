import { NextRequest, NextResponse } from 'next/server'

export async function GET(req: NextRequest) {
  const word = req.nextUrl.searchParams.get('text') || ''
  if (!word.trim()) return NextResponse.json({ suggestions: [] })

  const url = `https://inputtools.google.com/request?text=${encodeURIComponent(word.toLowerCase())}&itc=hi-t-i0-und&num=5&cp=0&cs=1&ie=utf-8&oe=utf-8&app=demopage`

  try {
    const resp = await fetch(url)
    const data = await resp.json()
    const suggestions: string[] =
      data && data[0] === 'SUCCESS' && data[1]?.[0]?.[1]
        ? data[1][0][1]
        : []
    return NextResponse.json({ suggestions })
  } catch {
    return NextResponse.json({ suggestions: [] })
  }
}
