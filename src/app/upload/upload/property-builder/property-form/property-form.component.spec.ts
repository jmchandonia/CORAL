import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { Select2Module } from 'ng2-select2';
import { TooltipModule } from 'ngx-bootstrap/tooltip';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { BsModalService } from 'ngx-bootstrap/modal';
import { PropertyFormComponent } from './property-form.component';
import { TypedProperty } from 'src/app/shared/models/brick';

describe('PropertyFormComponent', () => {
  let spectator: Spectator<PropertyFormComponent>;
  const createComponent = createComponentFactory({
    component: PropertyFormComponent,
    imports: [
      Select2Module,
      TooltipModule.forRoot(),
      FormsModule,
      HttpClientModule
    ],
    providers: [
      BsModalService
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {
      property: new TypedProperty(0, true)
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
