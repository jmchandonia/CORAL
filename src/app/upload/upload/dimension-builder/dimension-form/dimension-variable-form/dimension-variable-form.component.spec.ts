import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { DimensionVariableFormComponent } from './dimension-variable-form.component';
import { Select2Module } from 'ng2-select2';
import { TooltipModule } from 'ngx-bootstrap/tooltip';
import { ModalModule } from 'ngx-bootstrap/modal';
import { HttpClientModule } from '@angular/common/http';
import { DimensionVariable, BrickDimension, Brick } from 'src/app/shared/models/brick';

describe('DimensionVariableFormComponent', () => {
  let spectator: Spectator<DimensionVariableFormComponent>;
  const createComponent = createComponentFactory({
    component: DimensionVariableFormComponent,
    imports: [
      Select2Module,
      TooltipModule.forRoot(),
      HttpClientModule,
      ModalModule.forRoot()
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {
      dimVar: new DimensionVariable(
        new BrickDimension(new Brick(), 0),
        0,
        true
      )
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
