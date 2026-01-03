import flet as ft
from src.auth.auth_handler import AuthHandler

# We wrap the UI in a class so we can pass the 'page' and 'auth' easily
class AdminDashboard:
    def __init__(self, page: ft.Page, auth: AuthHandler, on_logout):
        self.page = page
        self.auth = auth
        self.on_logout = on_logout
        self.pending_list_view = ft.ListView(expand=True, spacing=10)

    def build(self):
        # 1. Fetch data immediately
        pending_emails = self.auth.get_pending_operators()
        
        # 2. Populate the list
        self.refresh_list(pending_emails)

        # 3. Create the Main Layout
        return ft.View(
            "/admin",
            controls=[
                # --- Header ---
                ft.Container(
                    padding=20,
                    bgcolor=ft.colors.BLUE_GREY_900,
                    border_radius=ft.border_radius.only(bottom_left=15, bottom_right=15),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column([
                                ft.Text("Admin Dashboard", size=24, weight="bold", color="white"),
                                ft.Text(f"Welcome, {self.auth.SUPER_ADMIN}", size=12, color="white70")
                            ]),
                            ft.IconButton(ft.icons.LOGOUT, icon_color="red", on_click=lambda e: self.on_logout())
                        ]
                    )
                ),
                
                # --- Title ---
                ft.Container(
                    padding=ft.padding.only(left=20, top=20),
                    content=ft.Text("Pending Approvals", size=20, weight="bold", color="black")
                ),

                # --- The List of Cards ---
                ft.Container(
                    expand=True,
                    padding=20,
                    content=self.pending_list_view
                )
            ],
            bgcolor=ft.colors.GREY_50 # Light background for the whole screen
        )

    def refresh_list(self, emails):
        self.pending_list_view.controls.clear()
        
        if not emails:
            # Show "All Caught Up" Empty State
            self.pending_list_view.controls.append(
                ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, size=80, color="green"),
                        ft.Text("All caught up!", size=20, color="grey"),
                        ft.Text("No pending operator requests.", size=14, color="grey")
                    ]
                )
            )
        else:
            # Create a card for each email
            for email in emails:
                self.pending_list_view.controls.append(self.create_user_card(email))
        
        self.page.update()

    def create_user_card(self, email):
        # Logic to handle the click
        def on_approve_click(e):
            success = self.auth.approve_operator(email)
            if success:
                # OPTIMISTIC UPDATE: Remove card immediately
                # e.control is the button, .parent is the Row, .parent is the Container, .parent is the Card
                # We need to find the specific control in the list view to remove it.
                # Easiest way in Flet logic:
                
                # 1. Remove this specific card instance from the list controls
                self.pending_list_view.controls.remove(card_component)
                
                # 2. Check if list is empty now
                if len(self.pending_list_view.controls) == 0:
                     self.refresh_list([]) # Show empty state
                
                # 3. Show Success SnackBar
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Approved {email}"), bgcolor="green")
                self.page.snack_bar.open = True
                
                self.page.update()

        # The UI Card Design
        content = ft.Container(
            padding=15,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row([
                        ft.Icon(ft.icons.PERSON_ROUNDED, size=40, color="blue"),
                        ft.VerticalDivider(width=10, color="transparent"),
                        ft.Column([
                            ft.Text(email, weight="bold", size=16),
                            ft.Container(
                                bgcolor=ft.colors.ORANGE_100,
                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                border_radius=5,
                                content=ft.Text("Operator • Pending", size=10, color=ft.colors.ORANGE_800)
                            )
                        ], spacing=2),
                    ]),
                    
                    ft.ElevatedButton(
                        "Approve",
                        icon=ft.icons.CHECK,
                        bgcolor="green",
                        color="white",
                        elevation=0,
                        on_click=on_approve_click
                    )
                ]
            )
        )
        
        card_component = ft.Card(elevation=2, content=content, color="white")
        return card_component