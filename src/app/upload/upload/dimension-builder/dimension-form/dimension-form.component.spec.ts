import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { MockComponent } from 'ng-mocks';
import { Select2Module } from 'ng2-select2';
import { HttpClientModule } from '@angular/common/http';
import { DimensionFormComponent } from './dimension-form.component';
import { DimensionVariableFormComponent } from './dimension-variable-form/dimension-variable-form.component';
import { BrickDimension, Brick } from 'src/app/shared/models/brick';


describe('DimensionFormComponent', () => {

  let spectator: Spectator<DimensionFormComponent>;
  const createComponent = createComponentFactory({
    component: DimensionFormComponent,
    imports: [
      Select2Module,
      HttpClientModule
    ],
    entryComponents: [
      MockComponent(DimensionVariableFormComponent)
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {
      dimension: new BrickDimension(new Brick(), 0, true)
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
