import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormField, MatInput } from '@angular/material/input';
import { ChatComponent } from './chat/chat.component';
import { inject } from '@angular/core';
import {
  MatBottomSheet,
  MatBottomSheetModule,
} from '@angular/material/bottom-sheet';
import { delay } from 'rxjs';
import { ChatBubbleComponent } from './chat/chat-bubble/chat-bubble.component';
import { ToolResultsComponent } from './tool-results/tool-results.component';
import { MatIcon } from '@angular/material/icon';
import { HeaderComponent } from './header/header/header.component';
import { MatButton, MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    CommonModule,
    ChatBubbleComponent,
    FormsModule,
    MatInput,
    MatFormField,
    ChatComponent,
    ToolResultsComponent,
    MatBottomSheetModule,
    MatIcon,
    HeaderComponent,
    MatButton,
    MatButtonModule,
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  readonly bottomSheet = inject(MatBottomSheet);
  isOpen = false;

  open(): void {
    this.isOpen = true;
    const sheetRef = this.bottomSheet.open(ChatComponent, {
      panelClass: 'bottom-sheet-right',
      hasBackdrop: false,
      disableClose: false,
    });

    sheetRef
      .backdropClick()
      .pipe(delay(200))
      .subscribe(() => {
        this.isOpen = false;
      });
  }
}
