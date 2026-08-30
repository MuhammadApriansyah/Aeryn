export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const res = await fetch('http://127.0.0.1:3010/health');
    const data = await res.json();
    return Response.json(data);
  } catch (e: any) {
    return Response.json({ status: 'offline', error: e.message }, { status: 503 });
  }
}
