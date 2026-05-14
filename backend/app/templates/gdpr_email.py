def get_art14_html(candidate_name):
    return f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #09090b; color: #fafafa;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #09090b; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <!-- Container principale -->
                    <table width="100%" max-width="600" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #18181b; border: 1px solid #27272a; border-radius: 24px; overflow: hidden; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);">
                        
                        <!-- Header con Logo -->
                        <tr>
                            <td style="padding: 40px 40px 20px 40px; text-align: left;">
                                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td width="40" style="background-color: #6366f1; border-radius: 8px; padding: 8px; text-align: center;">
                                            <span style="color: white; font-weight: bold; font-size: 18px;">F</span>
                                        </td>
                                        <td style="padding-left: 15px;">
                                            <span style="font-size: 20px; font-weight: 800; letter-spacing: -0.5px; color: #ffffff;">FluxHR</span>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Titolo e Saluto -->
                        <tr>
                            <td style="padding: 20px 40px;">
                                <h1 style="font-size: 24px; font-weight: 700; color: #ffffff; margin: 0;">Informativa Trattamento Dati</h1>
                                <p style="font-size: 16px; color: #a1a1aa; margin-top: 10px;">Gentile <strong>{candidate_name}</strong>,</p>
                                <p style="font-size: 14px; line-height: 1.6; color: #a1a1aa;">
                                    Ti confermiamo che il tuo profilo professionale è stato acquisito con successo nel nostro database tramite la piattaforma FluxHR. In conformità all'<strong>Art. 14 del GDPR</strong>, desideriamo informarti su come proteggiamo la tua privacy.
                                </p>
                            </td>
                        </tr>

                        <!-- Box Punti Chiave -->
                        <tr>
                            <td style="padding: 0 40px;">
                                <div style="background-color: #09090b; border: 1px solid #27272a; border-radius: 16px; padding: 25px;">
                                    <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                        <tr>
                                            <td style="padding-bottom: 15px;">
                                                <span style="color: #6366f1; font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">Finalità</span>
                                                <div style="color: #ffffff; font-size: 14px; margin-top: 4px;">Ricerca e selezione del personale.</div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding-bottom: 15px;">
                                                <span style="color: #6366f1; font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">Conservazione</span>
                                                <div style="color: #ffffff; font-size: 14px; margin-top: 4px;">I dati saranno conservati per un periodo di 6 mesi.</div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td>
                                                <span style="color: #6366f1; font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">Protezione</span>
                                                <div style="color: #ffffff; font-size: 14px; margin-top: 4px;">Il nostro sistema ha già provveduto alla sanitizzazione automatica di eventuali dati sensibili non necessari.</div>
                                            </td>
                                        </tr>
                                    </table>
                                </div>
                            </td>
                        </tr>

                        <!-- Call to Action -->
                        <tr>
                            <td align="center" style="padding: 40px;">
                                <a href="#" style="background-color: #6366f1; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 12px; font-weight: 600; font-size: 14px; display: inline-block;">Gestisci i tuoi Dati</a>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #09090b; padding: 30px 40px; text-align: center; border-top: 1px solid #27272a;">
                                <p style="font-size: 12px; color: #71717a; margin: 0;">
                                    Ricevi questa mail perché hai inviato la tua candidatura a una delle aziende partner di FluxHR.<br><br>
                                    FluxHR Privacy Team &bull; Regolamento UE 2016/679
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """