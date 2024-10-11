import {Component, inject, OnInit} from '@angular/core';
import {MatBottomSheet} from "@angular/material/bottom-sheet";
import {ChatComponent} from "../chat/chat.component";
import {delay} from "rxjs";
import {HeaderComponent} from "../header/header/header.component";
import {MatIcon} from "@angular/material/icon";
import {MatIconButton} from "@angular/material/button";
import {RouterOutlet} from "@angular/router";
import {ToolResultsComponent} from "../tool-results/tool-results.component";
import {AuthService} from "../service/auth.service";
import {User} from "oidc-client-ts";
import {AssistantService} from "../service/assistant.service";

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    HeaderComponent,
    MatIcon,
    MatIconButton,
    RouterOutlet,
    ToolResultsComponent
  ],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss'
})
export class HomeComponent implements OnInit{
  currentUser: User | null = null;
  readonly bottomSheet = inject(MatBottomSheet);
  isOpen = false;

  constructor(private authService: AuthService, private assistantService: AssistantService) {
  }

  ngOnInit(): void {
    this.authService.getReadySubject().subscribe(ready=> {
      console.log(`ready:${ready}`)
      if(!ready){
        console.log("home: auth service not ready, returning")
        return
      }
      this.authService.getUser().then(user => {
        this.currentUser = user;

        if (user && user.id_token) {
          console.log('User Logged In');
          this.open()
          this.assistantService.initialize(user.id_token).then(r => {
              this.assistantService.stream(
                "provide a greeting for a returning user with a short company overview from 1st April 2023 to 31st March 2024, " +
                "Start your response with the welcome addressing the user",
                false)
            }
          );
        } else {
          console.log('User Not Logged In');
          const urlParams = new URLSearchParams(window.location.search);
          const redirect = urlParams.get('redirect_uri')

          this.authService.login().catch(err => {
            console.log(err);
          });
        }


      }).catch(err => console.log(err));
    })

  }


  open(): void {
    this.isOpen = true;
    const sheetRef = this.bottomSheet.open(ChatComponent, {
      backdropClass: 'bottom-sheet-overlay',
      hasBackdrop: false,
    });

    sheetRef
      .backdropClick()
      .pipe(delay(200))
      .subscribe(() => {
        this.isOpen = false;
      });
  }
}
