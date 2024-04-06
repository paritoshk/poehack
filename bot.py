from __future__ import annotations

from typing import AsyncIterable

import os
import fal_client
import fastapi_poe as fp
from fastapi_poe.types import (
    PartialResponse,
    ProtocolMessage,
    QueryRequest,
    SettingsRequest,
    SettingsResponse,
)
import httpx
from dataclasses import dataclass
from anthropic import Anthropic

POE_ACCESS_KEY = os.getenv("POE_ACCESS_KEY")
FAL_KEY = os.getenv("FAL_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


class MotivationalCoach(fp.PoeBot):
    def __post_init__(self) -> None:
        super().__post_init__()
        self.fal_client = fal_client.AsyncClient(key=FAL_KEY)
        self.http_client = httpx.AsyncClient()
        self.claude_client = Anthropic()

    async def get_claude_output(self, user_prompt: str) -> str:
        client = self.claude_client
        # System prompt to guide the AI's role and response style
        system_prompt = (
            "You are a friendly and motivational basketball coach for young athletes. "
            "Your goal is to inspire and encourage them in their early days of playing basketball. "
            "Engage in a conversation to learn about their gender/pronouns, age, city, practice times, goals, "
            "current coach, team dynamics, and emotions. Use this information to craft personalized, "
            "motivational messages that resonate with their experiences and aspirations."
        )

        # Example of creating a message flow with a user input and AI response
        response = client.messages.create(
            model="claude-3-opus-20240229",
            messages=[
                {"role": "user", "content": "Hello there."},
                {"role": "assistant", "content": "Hi, I'm Claude. How can I help you?"},
                {"role": "user", "content": f"{user_prompt}"}
            ],
            system=system_prompt,
            max_tokens=1024,
        )

        return response.content

    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        
        yield fp.MetaResponse(
            text="",
            content_type="text/markdown",
            linkify=True,
            refetch_settings=False,
            suggested_replies=False,
        )

        message = request.query[-1]
        prompt = message.content
        
        
        claude_output_response = await self.get_claude_output(prompt)
        claude_output = claude_output_response[len(claude_output_response) - 1].text

        response = await self.fal_client.run(
            "fal-ai/fast-sdxl",
            arguments={
                "prompt": f"{prompt}. I am seeking motivation. Please generate motivational images for me in the point of view of a young athlete",
                "negative_prompt": "cartoon, illustration, animation. face. male, female",
                "image_size": "square_hd",
                "num_inference_steps": 25,
                "guidance_scale": 7.5,
                "num_images": 1,
                "loras": [
                    {
                    "path": "https://storage.googleapis.com/fal_dreambooth/lora/3c0af85961b4080d/diffusers.safetensors?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=distributed-worker%40isolate-dev-hot-rooster.iam.gserviceaccount.com%2F20240406%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20240406T213926Z&X-Goog-Expires=54000&X-Goog-SignedHeaders=host&X-Goog-Signature=7295e3e9a4ff7aa2925bc60e9e4ad8ef24e1c69df17e6e6f3137804ae17e2c612c16ad1ad47a4085e4784158ff77a4876216a572e2071cd75a2b09d02159da6ac4e03ece9006b2ba7b5d81a6ea73c5f302987668aa5bffcf6dd795994aeeae0a0905f0497b47fdde4d85f7503b3fb1f9b61d1a09637cd2ada97212632c3adaeb146323032eb96da2723b0a40c238576e5d7c2fcb7fcaaceb9185bf9bea5ac3964022af881cef9e4512ceecb98a6a5475930b3ce76158c1b93a82bf82560e941e03818433c60d89fc0c72b514c1eba4dfb7271b293fa0fbb0b7c9532ab2714f0797dd16fb175dbfca3214e4e49da1d24cb1b53b8404efae5f79c088167e02c5bd"
                    }
                ],
                "embeddings": [
                    {
                    "path": "https://storage.googleapis.com/fal_dreambooth/lora/3c0af85961b4080d/emb.safetensors?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=distributed-worker%40isolate-dev-hot-rooster.iam.gserviceaccount.com%2F20240406%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20240406T213928Z&X-Goog-Expires=54000&X-Goog-SignedHeaders=host&X-Goog-Signature=53a4eec997acabf9e632ac997e8feedc3ebc8f60b18baae5f0879fd280762043cb93447fad5250dac0f0cab39ce4b338d45a9141656ca73b0376e4cb693ef73307856063ef7029eed8d3f2ccbb29a0efac2bad1464719e7788d1e0c6376d42fbd57aaf6e1d3778a547170c415f7616524d2471fbae386067abb0e288e137db233c323134deb70fde0a60948410bc245b0a6f466ff8fae63f14d7425c15c9f5754465eaffd5db5687c97881a76ac16df2cca1bbafd699a320a8d5e1e1e875666044fe05bdfc31822e81c48a30b3ed23be9a7e0454c9d1d1dabed1725634c0bcc9596e99c56963886a4a87a1268a52e62c0bf9768a65ff2b3258acc2d7f4895fe3"
                    }
                ],
                "format": "jpeg",
                "enable_safety_checker": True
            },
        )
        yield fp.PartialResponse(text="")

        image_url = response["images"][0]["url"]
        await self.post_message_attachment(
            message_id=request.message_id,
            download_url=image_url
        )
        yield fp.PartialResponse(text=f"", is_replace_response=True)
        yield fp.PartialResponse(text=f"{claude_output}", is_replace_response=False)

       

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(
            allow_attachments=False,
            introduction_message=(
                "Welcome to the motivational bot."
            )
           # server_bot_dependencies={"Claude-3-Opus": 1}
        )


bot = MotivationalCoach()
app = fp.make_app(bot, POE_ACCESS_KEY)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
