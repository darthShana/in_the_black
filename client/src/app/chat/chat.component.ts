import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  OnInit,
  ViewChild,
} from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatFormField } from '@angular/material/form-field';
import { MatInput } from '@angular/material/input';
import { CommonModule, NgForOf } from '@angular/common';
import { v4 as uuid } from 'uuid';
import { Subject, takeUntil } from 'rxjs';
import { AssistantService } from '../service/assistant.service';
import { ChatBubbleComponent } from './chat-bubble/chat-bubble.component';
import { MatBottomSheetRef } from '@angular/material/bottom-sheet';
import { MatIcon } from '@angular/material/icon';
import { MatButton, MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [
    CommonModule,
    ChatBubbleComponent,
    FormsModule,
    MatFormField,
    MatInput,
    NgForOf,
    ReactiveFormsModule,
    MatIcon,
    MatButtonModule,
    MatButton,
  ],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss',
})
export class ChatComponent implements OnInit, AfterViewInit, OnDestroy {
  title = 'client-app';
  conversationOrder: string[] = [];
  conversationMap?: Map<
    string,
    Record<string, unknown & { content: { text: string }[] & any }>
  >;

  @ViewChild('textChain') textChainRef?: ElementRef;
  @ViewChild('textChainWrapper') textChainWrapperRef?: ElementRef;

  user_id: string = uuid();
  unsubscribe: Subject<void> = new Subject();

  constructor(
    private assistantService: AssistantService,
    private bottomSheetRef: MatBottomSheetRef<ChatComponent>
  ) {
    console.log('CONSTRUCT');
    this.user_id = 'user_id';
  }

  ngOnDestroy(): void {
    this.unsubscribe.next();
    this.unsubscribe.complete();
  }

  async ngOnInit() {
    console.log('INIT');

    await this.assistantService.initialize(this.user_id);

    this.assistantService.conversationOrderSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe((result) => {
        console.log(result);
        this.conversationOrder = result;
      });

    this.assistantService.streamResultsSubject
      .pipe(takeUntil(this.unsubscribe))
      .subscribe((result) => {
        // console.log(result);
        this.conversationMap = result;
      });
  }

  ngAfterViewInit(): void {
    const observer = new ResizeObserver((entries) => {
      entries.forEach((entry) => {
        // console.log("scroll", entry);
        if (this.textChainWrapperRef) {
          this.textChainWrapperRef.nativeElement.scrollTop =
            this.textChainWrapperRef?.nativeElement.scrollHeight;
        }
      });
    });

    observer.observe(this.textChainRef?.nativeElement);
  }

  protected stream(query: string) {
    this.assistantService.stream(query).then((r) => console.log('stream done'));
  }

  closeBottomSheet(): void {
    this.bottomSheetRef.dismiss();
  }
}
