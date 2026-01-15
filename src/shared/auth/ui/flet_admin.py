"""Flet admin dashboard UI component."""

import flet as ft

from src.shared.auth.application.services.UserService import UserService
from src.shared.auth.infrastructure.repositories.UserRepository import SqliteUserRepository


class AdminDashboard:
    """
    Flet-based admin dashboard for operator approval.
    Uses UserService from application layer.
    """
    
    def __init__(self, page: ft.Page, admin_email: str, on_logout):
        self.page = page
        self.admin_email = admin_email
        self.on_logout = on_logout
        self.pending_list_view = ft.ListView(expand=True, spacing=10)
        
        # Initialize service
        user_repo = SqliteUserRepository()
        self.user_service = UserService(user_repo)

    def build(self):
        """Build admin dashboard view."""
        # Fetch pending operators
        pending_operators = self.user_service.get_pending_operators()
        self.refresh_list(pending_operators)

        # Create main layout
        return ft.View(
            "/admin",
            controls=[
                # Header
                ft.Container(
                    padding=20,
                    bgcolor=ft.colors.BLUE_GREY_900,
                    border_radius=ft.border_radius.only(bottom_left=15, bottom_right=15),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column([
                                ft.Text("Admin Dashboard", size=24, weight="bold", color="white"),
                                ft.Text(f"Welcome, {self.admin_email}", size=12, color="white70")
                            ]),
                            ft.IconButton(
                                ft.icons.LOGOUT,
                                icon_color="red",
                                on_click=lambda e: self.on_logout()
                            )
                        ]
                    )
                ),
                
                # Title
                ft.Container(
                    padding=ft.padding.only(left=20, top=20),
                    content=ft.Text("Pending Approvals", size=20, weight="bold", color="black")
                ),

                # List of pending operators
                ft.Container(
                    expand=True,
                    padding=20,
                    content=self.pending_list_view
                )
            ],
            bgcolor=ft.colors.GREY_50
        )

    def refresh_list(self, operators: list):
        """Refresh the list of pending operators."""
        self.pending_list_view.controls.clear()
        
        if not operators:
            # Show empty state
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
            # Create card for each pending operator
            for email, station_label in operators:
                self.pending_list_view.controls.append(
                    self.create_user_card(email, station_label)
                )
        
        self.page.update()

    def create_user_card(self, email: str, station_label: str):
        """Create approval card for pending operator."""
        def on_approve_click(_):
            success = self.user_service.approve_operator(email)
            if success:
                # Remove card from list
                self.pending_list_view.controls.remove(card_component)
                
                # Check if list empty
                if len(self.pending_list_view.controls) == 0:
                    self.refresh_list([])
                
                # Show success message
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"Approved {email}"),
                    bgcolor="green"
                )
                self.page.snack_bar.open = True
                self.page.update()
            else:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("Approval failed"),
                    bgcolor="red"
                )
                self.page.snack_bar.open = True
                self.page.update()

        def on_reject_click(_):
            success = self.user_service.reject_operator(email)
            if success:
                # Remove card
                self.pending_list_view.controls.remove(card_component)
                
                if len(self.pending_list_view.controls) == 0:
                    self.refresh_list([])
                
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"Rejected {email}"),
                    bgcolor="orange"
                )
                self.page.snack_bar.open = True
                self.page.update()

        card_component = ft.Card(
            elevation=2,
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.icons.PERSON, color="blue"),
                        ft.Column([
                            ft.Text(email, weight="bold", size=16),
                            ft.Text(f"Station: {station_label}", size=12, color="grey")
                        ], spacing=2)
                    ]),
                    ft.Divider(),
                    ft.Row([
                        ft.ElevatedButton(
                            "Approve",
                            icon=ft.icons.CHECK,
                            color="white",
                            bgcolor="green",
                            on_click=on_approve_click
                        ),
                        ft.OutlinedButton(
                            "Reject",
                            icon=ft.icons.CLOSE,
                            on_click=on_reject_click
                        )
                    ], alignment=ft.MainAxisAlignment.END)
                ])
            )
        )
        
        return card_component
