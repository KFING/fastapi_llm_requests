# fastapi_llm_requests

**exclude exception**: Translate, but do not translate text inside "<keep>"..."</keep>" tags.

**prompt tamplate**: Translate the following text into {lang_abbr}. Use the provided context to maintain meaning and tone. Do not translate or modify any parts listed in 'exclude'.\n\n Context:\n{context}\n\n Exclude:\n{exclude}\n\n Text:\n{text}\n\n Output only the translated text without any explanations or formatting.

**lang_abbr**: en, English, angelsky, belarus, by, poland language, polsky, etc. So it is just str param

Download everything that is in poetry, you can use, for example: poetry lock, poetry install
Than you can run redis from docker compose file, please check PORT in docker-compose file
