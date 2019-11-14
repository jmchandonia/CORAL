import { Component, OnInit } from '@angular/core';
import { Context } from 'src/app/shared/models/brick';

@Component({
  selector: 'app-context-builder',
  templateUrl: './context-builder.component.html',
  styleUrls: ['./context-builder.component.css']
})
export class ContextBuilderComponent implements OnInit {

  private context: Context[];

  constructor() { }

  ngOnInit() {
    console.log('THIS DOT CONTEXT', this.context);
  }

  addContext() {
    this.context.push(new Context(false));
  }

  removeContext(index: number): void {
    this.context.splice(index, 1);
  }

  resetContext(event: Context, index: number) {
    this.context.splice(index, 1, event);
  }

}
