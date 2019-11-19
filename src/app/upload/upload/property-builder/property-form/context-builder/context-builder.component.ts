import { Component, OnInit } from '@angular/core';
import { Context } from 'src/app/shared/models/brick';
import { BsModalRef } from 'ngx-bootstrap/modal';

@Component({
  selector: 'app-context-builder',
  templateUrl: './context-builder.component.html',
  styleUrls: ['./context-builder.component.css']
})
export class ContextBuilderComponent implements OnInit {

  public context: Context[];
  public title: string;

  constructor(
    public modalRef: BsModalRef
  ) { }

  ngOnInit() {
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
