import { createBrowserRouter } from "react-router-dom"
import { RootLayout } from "@/layouts"
import { HomePage, NotFoundPage } from "@/pages"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
])
